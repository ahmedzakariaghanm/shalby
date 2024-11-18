# إضافة جميع التحسينات المذكورة أعلاه
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN غير محدد في ملف .env")

reminders = {}
user_data = {}

async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data[chat_id] = {}
    welcome_message = "مرحبًا! اختر التاريخ للتذكير."
    keyboard = [[InlineKeyboardButton((datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=f"date:{(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')}")] for i in range(7)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data.startswith("date:"):
        user_data[chat_id]['date'] = data.split(":")[1]
        keyboard = [[InlineKeyboardButton(f"{hour}:00", callback_data=f"time:{hour}:00")] for hour in range(9, 21)]
        await query.edit_message_text("اختر الوقت:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("time:"):
        user_data[chat_id]['time'] = data.split(":")[1]
        await query.edit_message_text("الآن، اكتب وصف التذكير:")

    elif update.message.text:
        description = update.message.text
        if 'date' in user_data[chat_id] and 'time' in user_data[chat_id]:
            date_time = f"{user_data[chat_id]['date']} {user_data[chat_id]['time']}"
            reminder_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
            reminders[chat_id] = reminders.get(chat_id, [])
            reminders[chat_id].append({"time": reminder_time, "description": description})
            await update.message.reply_text(f"تم إضافة التذكير: {description} في {reminder_time}")
        else:
            await update.message.reply_text("حدث خطأ أثناء إعداد التذكير.")
        user_data.pop(chat_id, None)

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in reminders and reminders[chat_id]:
        reminder_list = "\n".join([f"{i+1}. {r['description']} - {r['time'].strftime('%Y-%m-%d %H:%M')}" for i, r in enumerate(reminders[chat_id])])
        await update.message.reply_text(f"تذكيراتك الحالية:\n{reminder_list}")
    else:
        await update.message.reply_text("لا توجد تذكيرات حالية.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_reminder))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("list_reminders", list_reminders))
    print("Bot is running...")
    app.run_polling()
