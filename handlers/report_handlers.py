# handlers/report_handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import requests
import pandas as pd

from helpers import calculate_date_range
from config import BACKEND_URL

async def non_custom_report(update: Update, context: CallbackContext, user_input, reply_markup):
    token = context.user_data['token']
    print(user_input)
    start_date, end_date = calculate_date_range(user_input)
    print(start_date)
    print(end_date)
    if start_date and end_date:
        response = requests.get(
            f"{BACKEND_URL}/admin/report/",
            headers={'Authorization': f'Bearer {token}'},
            params={'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d')}
        )
        if response.status_code == 200:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=response.content,
                filename="Attendance_Report.xlsx"
            )
            await update.message.reply_text("Report generated successfully.", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Failed to generate report.")
    else:
        await update.message.reply_text("Invalid time frame option.")

async def handle_custom_dates(update: Update, context: CallbackContext, reply_markup):
    token = context.user_data.get('token')
    print("Handling")
    if not token:
        await update.message.reply_text("You need to authenticate first. Please start again.")
        return

    start_date = context.user_data.get('start_date')
    end_date = context.user_data.get('end_date')

    try:
        pd.to_datetime(start_date, format='%Y-%m-%d')
        pd.to_datetime(end_date, format='%Y-%m-%d')
        
        response = requests.get(
            f"{BACKEND_URL}/admin/report/",
            headers={'Authorization': f'Bearer {token}'},
            params={'start_date': start_date, 'end_date': end_date}
        )
        if response.status_code == 200:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=response.content,
                filename="Attendance_Report.xlsx"
            )
            await update.message.reply_text("Report generated successfully.", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Failed to generate report.")
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD format.")

    context.user_data['report_option'] = None
    context.user_data.pop('start_date', None)
    
