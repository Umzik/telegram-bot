from telegram import Update, Location, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
import requests

from config import BACKEND_URL

async def request_location(update: Update):
    location_button = KeyboardButton(text="Joylashuvni ulashish", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True)
    
    await update.message.reply_text("Kirish/chiqish uchun joylashuvni kiriting.", reply_markup=reply_markup)

async def checkin(update: Update, context: CallbackContext, reply_markup):
    token = context.user_data.get('token')
    if not token:
        await update.message.reply_text("Avval siz autentifikatsiya qilishingiz kerak. Iltimos, qaytadan boshlang.", reply_markup=ReplyKeyboardMarkup([["Авторизация"]], one_time_keyboard=True, resize_keyboard=True))
        return
    
    context.user_data['last_action'] = 'checkin'

    location: Location = update.message.location
    if not location:
        await request_location(update)
        return

    response = requests.post(
        f"{BACKEND_URL}/checkin/",
        headers={'Authorization': f'Bearer {token}'},
        json={'latitude': location.latitude, 'longitude': location.longitude}
    )
    if response.status_code == 401:
        await update.message.reply_text("Avval siz autentifikatsiya qilishingiz kerak. Iltimos, qaytadan boshlang.",
                                        reply_markup=ReplyKeyboardMarkup([["Авторизация"]], one_time_keyboard=True,
                                                                         resize_keyboard=True))
        return

    await update.message.reply_text(response.json().get("message"), reply_markup=reply_markup)

async def checkout(update: Update, context: CallbackContext, reply_markup):
    token = context.user_data.get('token')
    if not token:
        await update.message.reply_text("Avval siz autentifikatsiya qilishingiz kerak. Iltimos, qaytadan boshlang.", reply_markup=ReplyKeyboardMarkup([["Авторизация"]], one_time_keyboard=True, resize_keyboard=True))
        return

    # Check if the message contains location data
    location: Location = update.message.location
    if not location:
        await request_location(update)
        return

    response = requests.post(
        f"{BACKEND_URL}/checkout/",
        headers={'Authorization': f'Bearer {token}'},
        json={'latitude': location.latitude, 'longitude': location.longitude}
    )
    if response.status_code == 401:
        await update.message.reply_text("Avval siz autentifikatsiya qilishingiz kerak. Iltimos, qaytadan boshlang.",
                                        reply_markup=ReplyKeyboardMarkup([["Авторизация"]], one_time_keyboard=True,
                                                                         resize_keyboard=True))
        return

    await update.message.reply_text(response.json().get("message"), reply_markup=reply_markup)
