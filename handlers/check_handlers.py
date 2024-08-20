from telegram import Update, Location
from telegram.ext import CallbackContext
import requests

from config import BACKEND_URL

async def checkin(update: Update, context: CallbackContext):
    token = context.user_data.get('token')
    if not token:
        await update.message.reply_text("You need to authenticate first. Please start again.")
        return

    # Automatically get the user's location
    location: Location = update.effective_message.location

    if not location:
        await update.message.reply_text("Failed to retrieve location. Please enable location services and try again.")
        return

    response = requests.post(
        f"{BACKEND_URL}/checkin/",
        headers={'Authorization': f'Bearer {token}'},
        json={'latitude': location.latitude, 'longitude': location.longitude}
    )

    await update.message.reply_text(response.json().get("message"))

async def checkout(update: Update, context: CallbackContext):
    token = context.user_data.get('token')
    if not token:
        await update.message.reply_text("You need to authenticate first. Please start again.")
        return

    # Automatically get the user's location
    location: Location = update.effective_message.location

    if not location:
        await update.message.reply_text("Failed to retrieve location. Please enable location services and try again.")
        return

    response = requests.post(
        f"{BACKEND_URL}/checkout/",
        headers={'Authorization': f'Bearer {token}'},
        json={'latitude': location.latitude, 'longitude': location.longitude}
    )

    await update.message.reply_text(response.json().get("message"))
