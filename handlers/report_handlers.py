import pandas as pd
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from config import BACKEND_URL
from helpers import calculate_date_range


async def non_custom_report(update: Update, context: CallbackContext, user_input, reply_markup):
    try:
        token = context.user_data['token']
        start_date, end_date = calculate_date_range(user_input)

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
                await update.message.reply_text("Hisobot muvaffaqiyatli yaratildi.", reply_markup=reply_markup)
            else:
                await update.message.reply_text(f"Hisobot yaratib bo‘lmadi. Status kodi: {response.status_code}",
                                                reply_markup=reply_markup)
        else:
            await update.message.reply_text("Vaqt oralig‘i noto‘g‘ri.", reply_markup=reply_markup)

    except requests.RequestException as req_err:
        await update.message.reply_text(f"Hisobotni yaratishda tarmoq xatosi:{str(req_err)}",
                                        reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"Hisobotni yaratishda xatolik yuz berdi: {str(e)}",
                                        reply_markup=reply_markup)


async def handle_custom_dates(update: Update, context: CallbackContext, reply_markup):
    token = context.user_data.get('token')

    if not token:
        await update.message.reply_text("Avval siz autentifikatsiya qilishingiz kerak. Iltimos, qaytadan boshlang.",
                                        reply_markup=ReplyKeyboardMarkup([["Avtorizasiya"]], one_time_keyboard=True,
                                                                         resize_keyboard=True))
        return

    start_date = context.user_data.get('start_date')
    end_date = context.user_data.get('end_date')

    try:
        # Validate date formats
        start_date_obj = pd.to_datetime(start_date, format='%Y-%m-%d', errors='raise')
        end_date_obj = pd.to_datetime(end_date, format='%Y-%m-%d', errors='raise')

        response = requests.get(
            f"{BACKEND_URL}/admin/report/",
            headers={'Authorization': f'Bearer {token}'},
            params={'start_date': start_date_obj.strftime('%Y-%m-%d'), 'end_date': end_date_obj.strftime('%Y-%m-%d')}
        )

        if response.status_code == 200:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=response.content,
                filename="Attendance_Report.xlsx"
            )
            await update.message.reply_text("Hisobot muvaffaqiyatli yaratildi.", reply_markup=reply_markup)
        else:
            await update.message.reply_text(f"Hisobot yaratib bo‘lmadi. Status kodi:{response.status_code}",
                                            reply_markup=reply_markup)

    except ValueError:
        await update.message.reply_text("Sana formati yaroqsiz. YYYY-MM-DD formatidan foydalaning.",
                                        reply_markup=reply_markup)

    except requests.RequestException as req_err:
        await update.message.reply_text(f"Hisobotni yaratishda tarmoq xatosi: {str(req_err)}",
                                        reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"Hisobotni yaratishda xatolik yuz berdi: {str(e)}",
                                        reply_markup=reply_markup)

    finally:
        # Clear report-related data
        context.user_data['report_option'] = None
        context.user_data.pop('start_date', None)
        context.user_data.pop('end_date', None)
