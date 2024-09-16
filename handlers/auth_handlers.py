import logging

import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from config import BACKEND_URL
from handlers.check_handlers import checkin, checkout, request_location
from handlers.report_handlers import non_custom_report, handle_custom_dates
from helpers import get_user_token, TIME_FRAME_OPTIONS


async def start(update: Update, context: CallbackContext):
    try:
        context.user_data.clear()
        context.user_data['auth_stage'] = 'start'
        await update.message.reply_text(
            "Botga hush kelibsiz. Avtarizasiya uchun tugmani bosing:",
            reply_markup=ReplyKeyboardMarkup([["Avtorizasiya"]], one_time_keyboard=True, resize_keyboard=True)
        )
    except Exception as e:
        await update.message.reply_text(f"Xato: {str(e)}")


def get_keyboard(role):
    try:
        return [["Kelish", "Ketish"], ["Admin Panel"], ["Hisobot yaratish"],["Parol o'zgartirish"], ["Akkauntdan chiqish"]] if role == 'admin' else [["Kelish", "Ketish"],["Parol o'zgartirish"], ["Akkauntdan chiqish"]]
    except Exception as e:
        return [["Akkauntdan chiqish"]]  # Fallback keyboard


async def send_reply(update: Update, text: str, context: CallbackContext, role=None):
    try:
        keyboard = get_keyboard(role or context.user_data.get('role'))
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Javob jo'natishda xatolik yuz berdi: {str(e)}")

async def handle_admin_checkin_checkout(update: Update, context: CallbackContext):
    try:
        # Fetch users from the backend
        token = context.user_data.get('token')
        response = requests.get(f"{BACKEND_URL}/users/", headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            users = response.json()
            # Create a list of users to display as buttons
            user_buttons = [[user['first_name'] + " " + user['last_name']] for user in users]
            user_buttons.append(["Bekor qilish"])
            reply_markup = ReplyKeyboardMarkup(user_buttons, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Biror foydalanuvchini tanlang:", reply_markup=reply_markup)
            context.user_data['stage'] = 'admin_user_selection'
            context.user_data['users'] = users
        else:
            await update.message.reply_text("Foydalanuvchilarni olishda xatolik yuz berdi.")
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")


async def handle_user_selection(update: Update, context: CallbackContext):
    try:
        selected_user = update.message.text
        if selected_user == "Bekor qilish":
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            await update.message.reply_text("Amaliyot bekor qilindi.", reply_markup=ReplyKeyboardMarkup(
                get_keyboard(context.user_data.get('role')), resize_keyboard=True))
            return

        # Find the selected user from the list
        users = context.user_data.get('users', [])
        for user in users:
            if f"{user['first_name']} {user['last_name']}" == selected_user:
                context.user_data['selected_user'] = user
                break

        # Provide check-in and check-out options
        reply_markup = ReplyKeyboardMarkup([["Ishchi kelishi", "Ishchi ketishi"], ["Bekor qilish"]], one_time_keyboard=True,
                                           resize_keyboard=True)
        await update.message.reply_text(f"{selected_user} uchun amalni tanlang:", reply_markup=reply_markup)
        context.user_data['stage'] = 'admin_action_selection'
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")

async def handle_admin_action_selection(update: Update, context: CallbackContext):
    try:
        action = update.message.text
        selected_user = context.user_data.get('selected_user')
        if not selected_user:
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            await update.message.reply_text("Foydalanuvchi tanlanmagan.", reply_markup=ReplyKeyboardMarkup(get_keyboard(context.user_data.get('role')), resize_keyboard=True))
            return

        if action == "Ishchi kelishi":
            # Send check-in request to backend
            await admin_checkin_checkout_backend(update, context, selected_user['id'], 'check_in')
        elif action == "Ishchi ketishi":
            # Send check-out request to backend
            await admin_checkin_checkout_backend(update, context, selected_user['id'], 'check_out')
        elif action == "Bekor qilish":
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            await update.message.reply_text("Amaliyot bekor qilindi.", reply_markup=ReplyKeyboardMarkup(get_keyboard(context.user_data.get('role')), resize_keyboard=True))
        else:
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            await update.message.reply_text("Noto'g'ri amal tanlandi.")
    except Exception as e:
        context.user_data.pop('selected_user', None)
        context.user_data.pop('stage', None)
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")


async def admin_checkin_checkout_backend(update: Update, context: CallbackContext, user_id, action):
    try:
        token = context.user_data.get('token')
        response = requests.post(
            f"{BACKEND_URL}/admin/check/",
            headers={'Authorization': f'Bearer {token}'},
            json={'employee_id': user_id, 'action': action}
        )
        if response.status_code == 200:
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            await update.message.reply_text(f"{action.capitalize()} muvaffaqiyatli bajarildi.")
        else:
            # Extract error message from backend response
            context.user_data.pop('selected_user', None)
            context.user_data.pop('stage', None)
            error_message = response.json().get('message', 'Xatolik yuz berdi.')
            await update.message.reply_text(f"{action.capitalize()}da xatolik: {error_message}")
    except Exception as e:
        context.user_data.pop('selected_user', None)
        context.user_data.pop('stage', None)
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")



async def handle_change_password(update: Update, context: CallbackContext):
    try:
        new_pass_stage = context.user_data.get('new_pass_stage')
        user_input = update.message.text
        user_message_id = update.message.message_id

        # Step 1: Ask for the current password
        if new_pass_stage == 'start_change_password':
            context.user_data['new_pass_stage'] = 'current_password'
            await update.message.reply_text("Hozirgi parol:")

        # Step 2: Store the current password and ask for the new password
        elif new_pass_stage == 'current_password':
            context.user_data['current_password'] = user_input
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            context.user_data['new_pass_stage'] = 'new_password'
            await update.message.reply_text("Yangi parol:")

        # Step 3: Confirm the password change and call backend to update
        elif new_pass_stage == 'new_password':
            current_password = context.user_data.get('current_password')
            new_password = user_input
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)

            # Call the backend to change the password
            try:
                token = context.user_data.get('token')
                response = requests.post(
                    f"{BACKEND_URL}/user/change_password/",
                    headers={'Authorization': f'Bearer {token}'},
                    json={'current_password': current_password, 'new_password': new_password}
                )

                if response.status_code == 200:
                    await update.message.reply_text("Parolingiz muvaffaqiyattli o'zgartirildi.")
                else:
                    await update.message.reply_text("Parol o'zgartirilmadi. Qayta takrorlab ko'rin.")
            except Exception as e:
                await update.message.reply_text(f"Parol o'zgartirishta xatolik yuz berdi: {str(e)}")

            context.user_data['new_pass_stage'] = None

    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")

async def handle_auth(update: Update, context: CallbackContext):
    try:
        auth_stage = context.user_data.get('auth_stage')
        user_input = update.message.text
        user_message_id = update.message.message_id

        if user_input == "Avtorizasiya" and auth_stage == 'start':
            context.user_data['auth_stage'] = 'login'
            await update.message.reply_text("Loginingizni kiriting:")

        elif auth_stage == 'login':
            context.user_data['login'] = user_input
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            context.user_data['auth_stage'] = 'password'
            await update.message.reply_text("Parolingizni kiriting:")

        elif auth_stage == 'password':
            login = context.user_data.get('login')
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            password = user_input
            token_response = None
            try:
                if get_user_token(login, password):
                    token_response, role_response, name, surname = get_user_token(login, password)
            except Exception as e:
                await update.message.reply_text(f"Autentifikasiya jarayonida xatolik: {str(e)}")
                return

            if token_response:
                context.user_data.update(
                    {'token': token_response, 'role': role_response, 'auth_stage': 'completed', 'status': 'base'})
                await send_reply(update, "Siz avtorizasiyadan o'tdingiz. Ushbu buyruqlar ishlatishingiz mumkin:", context, role_response)
            else:
                await update.message.reply_text("Avtorizasiya yakunlanmadi! Qayta loginingizni kiriting.")
                context.user_data['auth_stage'] = 'login'

    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")


async def handle_checkin_checkout(update: Update, context: CallbackContext, action: str):
    try:
        context.user_data['last_action'] = action
        await request_location(update)
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi {action}: {str(e)}")


async def handle_report(update: Update, context: CallbackContext):
    try:
        context.user_data['stage'] = 'report'
        keyboard = [["Bugun", "Uch kunlik"], ["Haftalik", "Oylik"], ["Boshqa"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Vaqt oraliqini tanlang:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Hisobot yaratishda xatolik: {str(e)}")

async def start_change_password(update: Update, context: CallbackContext):
    context.user_data['new_pass_stage'] = 'start_change_password'
    await handle_change_password(update, context)

async def handle_message(update: Update, context: CallbackContext):
    try:
        auth_stage = context.user_data.get('auth_stage')
        stage = context.user_data.get('stage')
        role = context.user_data.get('role')
        new_pass_stage = context.user_data.get('new_pass_stage')
        reply_markup = ReplyKeyboardMarkup(get_keyboard(role), one_time_keyboard=True, resize_keyboard=True)
        user_input = update.message.text

        if auth_stage and auth_stage != 'completed':
            await handle_auth(update, context)
            return

        actions = {
            "Kelish": lambda: handle_checkin_checkout(update, context, 'check_in'),
            "Ketish": lambda: handle_checkin_checkout(update, context, 'check_out'),
            "Hisobot yaratish": lambda: handle_report(update, context),
            "Parol o'zgartirish": lambda: start_change_password(update, context),
            "Admin Panel": lambda: handle_admin_checkin_checkout(update, context),
            "Akkauntdan chiqish": lambda: update.message.reply_text("Siz sistemadan chiqdingiz. Qaytakirish uchu /start bosing.") or context.user_data.clear(),
        }

        if user_input in actions:
            await actions[user_input]()
            return

        if stage == 'admin_user_selection':
            await handle_user_selection(update, context)
        elif stage == 'admin_action_selection':
            await handle_admin_action_selection(update, context)

        if new_pass_stage:
            await handle_change_password(update, context)

        # Handling predefined report timeframes
        if stage == 'report' and user_input in ('Bugun', 'Uch kunlik', 'Haftalik', 'Oylik'):
            await non_custom_report(update, context, user_input, reply_markup)
            context.user_data['stage'] = None

        # Handling custom report date (start date)
        elif stage == 'report' and user_input == 'Boshqa':
            context.user_data['stage'] = 'report-custom'
            await update.message.reply_text("Iltimos, boshlanish sanani kiriting:")

        # Handling custom report date (end date)
        elif stage == 'report-custom':
            context.user_data['start_date'] = user_input
            context.user_data['stage'] = 'report-custom2'
            await update.message.reply_text("Iltimos, tugash sanani kiriting:")

        # Completing custom report generation
        elif stage == 'report-custom2':
            context.user_data['end_date'] = user_input
            await handle_custom_dates(update, context, get_keyboard(role))
            context.user_data['stage'] = None

    except Exception as e:
        reply_markup = ReplyKeyboardMarkup(get_keyboard(role), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"So‘rovingizni ko‘rib chiqishda xatolik yuz berdi: {str(e)}", reply_markup=reply_markup)


async def handle_location(update: Update, context: CallbackContext):
    try:
        role = context.user_data.get('role')
        last_action = context.user_data.get('last_action')
        reply_markup = ReplyKeyboardMarkup(get_keyboard(role), one_time_keyboard=True, resize_keyboard=True)

        if last_action == 'check_in':
            await checkin(update, context, reply_markup)
        elif last_action == 'check_out':
            await checkout(update, context, reply_markup)
        else:
            await update.message.reply_text("Iltimos, avval ro'yxatdan o'tish yoki chiqishni xohlaysizmi, ko'rsating.", reply_markup=reply_markup)
    except Exception as e:
        logging.log(e)
        await update.message.reply_text(f"Joylashuvni qayta ishlashda xatolik yuz berdi: {str(e)}", reply_markup=reply_markup)

