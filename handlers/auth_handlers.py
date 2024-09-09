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
            "Добро пожаловать в бот! Пожалуйста, выберите вариант:",
            reply_markup=ReplyKeyboardMarkup([["Авторизация"]], one_time_keyboard=True, resize_keyboard=True)
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


def get_keyboard(role):
    try:
        return [["Отметить приход", "Отметить уход"], ["Сгенерировать отчет"],["Поменять пароль"], ["Покинуть аккаунт"]] if role == 'admin' else [["Отметить приход", "Отметить уход"],["Поменять пароль"], ["Покинуть аккаунт"]]
    except Exception as e:
        return [["Покинуть аккаунт"]]  # Fallback keyboard


async def send_reply(update: Update, text: str, context: CallbackContext, role=None):
    try:
        keyboard = get_keyboard(role or context.user_data.get('role'))
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при отправке ответа: {str(e)}")


async def handle_change_password(update: Update, context: CallbackContext):
    try:
        new_pass_stage = context.user_data.get('new_pass_stage')
        user_input = update.message.text
        user_message_id = update.message.message_id

        # Step 1: Ask for the current password
        if new_pass_stage == 'start_change_password':
            context.user_data['new_pass_stage'] = 'current_password'
            await update.message.reply_text("Введите ваш текущий пароль:")

        # Step 2: Store the current password and ask for the new password
        elif new_pass_stage == 'current_password':
            context.user_data['current_password'] = user_input
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            context.user_data['new_pass_stage'] = 'new_password'
            await update.message.reply_text("Введите новый пароль:")

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
                    await update.message.reply_text("Ваш пароль был успешно изменен.")
                else:
                    await update.message.reply_text("Не удалось сменить пароль. Попробуйте еще раз.")
            except Exception as e:
                await update.message.reply_text(f"Произошла ошибка при смене пароля: {str(e)}")

            context.user_data['new_pass_stage'] = None

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def handle_auth(update: Update, context: CallbackContext):
    try:
        auth_stage = context.user_data.get('auth_stage')
        user_input = update.message.text
        user_message_id = update.message.message_id

        if user_input == "Авторизация" and auth_stage == 'start':
            context.user_data['auth_stage'] = 'login'
            await update.message.reply_text("Введите ваш логин:")

        elif auth_stage == 'login':
            context.user_data['login'] = user_input
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            context.user_data['auth_stage'] = 'password'
            await update.message.reply_text("Введите ваш пароль:")

        elif auth_stage == 'password':
            login = context.user_data.get('login')
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_message_id)
            password = user_input
            token_response = None
            try:
                if get_user_token(login, password):
                    token_response, role_response, name, surname = get_user_token(login, password)
            except Exception as e:
                await update.message.reply_text(f"Произошла ошибка при аутентификации: {str(e)}")
                return

            if token_response:
                context.user_data.update(
                    {'token': token_response, 'role': role_response, 'auth_stage': 'completed', 'status': 'base'})
                await send_reply(update, "Вы авторизованы! Теперь вы можете использовать следующие команды:", context, role_response)
            else:
                await update.message.reply_text("Авторизация не удалась! Введите логин еще раз.")
                context.user_data['auth_stage'] = 'login'

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")


async def handle_checkin_checkout(update: Update, context: CallbackContext, action: str):
    try:
        context.user_data['last_action'] = action
        await request_location(update)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка во время {action}: {str(e)}")


async def handle_report(update: Update, context: CallbackContext):
    try:
        context.user_data['stage'] = 'report'
        keyboard = [["Сегодня", "За 3 дня"], ["Неделя", "Месяц"], ["Другое"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Choose the time frame:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при формировании параметров отчета: {str(e)}")

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
            "Отметить приход": lambda: handle_checkin_checkout(update, context, 'check_in'),
            "Отметить уход": lambda: handle_checkin_checkout(update, context, 'check_out'),
            "Сгенерировать отчет": lambda: handle_report(update, context),
            "Поменять пароль": lambda: start_change_password(update, context),  # Trigger password change flow
            "Покинуть аккаунт": lambda: update.message.reply_text("Вы вышли из системы. Чтобы начать снова, нажмите /start.") or context.user_data.clear(),
        }

        if user_input in actions:
            await actions[user_input]()
            return

        if new_pass_stage:
            await handle_change_password(update, context)

        # Handling predefined report timeframes
        if stage == 'report' and user_input in ('Сегодня', 'За 3 дня', 'Неделя', 'Месяц'):
            await non_custom_report(update, context, user_input, reply_markup)
            context.user_data['stage'] = None

        # Handling custom report date (start date)
        elif stage == 'report' and user_input == 'Другое':
            context.user_data['stage'] = 'report-custom'
            await update.message.reply_text("Пожалуйста, введите дату начала:")

        # Handling custom report date (end date)
        elif stage == 'report-custom':
            context.user_data['start_date'] = user_input
            context.user_data['stage'] = 'report-custom2'
            await update.message.reply_text("Введите дату окончания:")

        # Completing custom report generation
        elif stage == 'report-custom2':
            context.user_data['end_date'] = user_input
            await handle_custom_dates(update, context, get_keyboard(role))
            context.user_data['stage'] = None

    except Exception as e:
        reply_markup = ReplyKeyboardMarkup(get_keyboard(role), one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"При обработке вашего запроса произошла ошибка: {str(e)}", reply_markup=reply_markup)


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
            await update.message.reply_text("Пожалуйста, укажите, хотите ли вы сначала зарегистрироваться или выписаться.", reply_markup=reply_markup)
    except Exception as e:
        logging.log(e)
        await update.message.reply_text(f"Произошла ошибка при обработке местоположения: {str(e)}", reply_markup=reply_markup)

