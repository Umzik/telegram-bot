# handlers/auth_handlers.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from handlers.check_handlers import checkin, checkout, request_location
from handlers.report_handlers import non_custom_report, handle_custom_dates
from helpers import get_user_token
from helpers import TIME_FRAME_OPTIONS, calculate_date_range

async def start(update: Update, context: CallbackContext):
    context.user_data.clear()
    
    context.user_data['auth_stage'] = 'start'
    keyboard = [["Authorize"]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True, 
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Welcome to the bot! Please choose an option:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: CallbackContext):
    auth_stage = context.user_data.get('auth_stage')
    stage = context.user_data.get('stage')
    role = context.user_data.get('role')

    user_input = update.message.text

    if user_input == "Authorize" and auth_stage == 'start':
        context.user_data['auth_stage'] = 'login'
        await update.message.reply_text("Please enter your login:")

    elif auth_stage == 'login':
        context.user_data['login'] = update.message.text
        context.user_data['auth_stage'] = 'password'
        await update.message.reply_text("Please enter your password:")

    elif auth_stage == 'password':
        login = context.user_data.get('login')
        password = update.message.text
        token, role_response = get_user_token(login, password)
        if token:
            context.user_data['token'] = token
            context.user_data['role'] = role_response
            context.user_data['auth_stage'] = 'completed'
            context.user_data['status']='base'
            if role_response == 'admin':
                keyboard = [
                ["Check In", "Check Out"],
                ["Generate Report"],
                ["Leave Account"]
            ]
            else:
                keyboard = [
                ["Check In", "Check Out"],
                ["Leave Account"]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                one_time_keyboard=True, 
                resize_keyboard=True
            )
            await update.message.reply_text(
                "You are authorized! You can now use the following commands:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("Authorization failed! Please enter your login again.")
            context.user_data['auth_stage'] = 'login'

    if user_input == "Check In":
        context.user_data['last_action']='check_in'
        await request_location(update)

    elif user_input == "Check Out":
        context.user_data['last_action']='check_out'
        await request_location(update)

    elif user_input == "Generate Report":
        context.user_data['stage'] = 'report'
        keyboard = [["Today", "Last 3 Days"],
                    [ "This Week", "This Month"],
                    [ "Custom"]]
        reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                one_time_keyboard=True, 
                resize_keyboard=True
            )
        await update.message.reply_text(
                "Choose the time frame",
                reply_markup=reply_markup
            )


    elif user_input == "Leave Account":
        context.user_data.clear()
        await update.message.reply_text("You have been logged out. To start again, press /start.")


    elif user_input in ('Today', 'Last 3 Days', 'This Week', 'This Month') and stage == 'report':
        if role == 'admin':
                keyboard = [
                ["Check In", "Check Out"],
                ["Generate Report"],
                ["Leave Account"]
            ]
        else:
            keyboard = [
            ["Check In", "Check Out"],
            ["Leave Account"]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        )
        context.user_data['stage']=None
        await non_custom_report(update, context, user_input, reply_markup)

    elif user_input == "Custom":
        context.user_data['stage'] = 'report-custom'
        await update.message.reply_text("Please enter the start date:")

    elif stage == 'report-custom':
        context.user_data['stage'] = 'report-custom2'
        context.user_data['start_date'] = update.message.text
        await update.message.reply_text("Please enter the end date:")

    elif stage == 'report-custom2':
        print("Beginning")
        context.user_data['stage'] = None
        context.user_data['end_date'] = update.message.text
        print("text", update.message.text)
        if role == 'admin':
                keyboard = [
                ["Check In", "Check Out"],
                ["Generate Report"],
                ["Leave Account"]
            ]
        else:
            keyboard = [
            ["Check In", "Check Out"],
            ["Leave Account"]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True
        )
        await handle_custom_dates(update, context, reply_markup)


async def handle_location(update: Update, context: CallbackContext):
    role = context.user_data.get('role')
    last_action = context.user_data.get('last_action')
    if role == 'admin':
        keyboard = [
        ["Check In", "Check Out"],
        ["Generate Report"],
        ["Leave Account"]
            ]
    else:
        keyboard = [
        ["Check In", "Check Out"],
        ["Leave Account"]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True, 
        resize_keyboard=True
    )
    if last_action == 'check_in':
        await checkin(update, context, reply_markup)
    elif last_action == 'check_out':
        await checkout(update, context, reply_markup)
    else:
        await update.message.reply_text("Please specify whether you want to check in or check out first.")