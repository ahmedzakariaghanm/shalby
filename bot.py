import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio

# تحميل المتغيرات البيئية
load_dotenv()

# الحصول على التوكن
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# تخزين البيانات
reminders = {}
notes = {}

# إرسال رسالة ترحيبية عند بدء البوت
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name  # الحصول على اسم المستخدم
    print(f"User {chat_id} started the bot with name: {user_name}.")

    # رسالة ترحيبية
    welcome_message = (
        f"مرحبًا {user_name}! 🎉\n"
        "أنا هنا لمساعدتك. ماذا تحتاج؟"
    )

    # عرض الاختيارات
    keyboard = [
        [InlineKeyboardButton("إضافة ملاحظة جديدة", callback_data="add_note")],
        [InlineKeyboardButton("عرض الملاحظات السابقة", callback_data="view_notes")],
        [InlineKeyboardButton("إضافة تذكرة جديدة", callback_data="add_reminder")],
        [InlineKeyboardButton("عرض التذكيرات السابقة", callback_data="view_reminders")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    print(f"User {chat_id} selected: {query.data}")

    if query.data == "add_note":
        await query.edit_message_text("يرجى كتابة الملاحظة التي تريد إضافتها:")
        context.user_data["action"] = "add_note"

    elif query.data == "view_notes":
        if chat_id in notes and notes[chat_id]:
            notes_text = "\n".join(notes[chat_id])
            await query.edit_message_text(f"ملاحظاتك السابقة:\n{notes_text}")
        else:
            await query.edit_message_text("لا توجد ملاحظات محفوظة.")

    elif query.data == "add_reminder":
        await query.edit_message_text("يرجى كتابة التذكرة التي تريد إضافتها مع الوقت بالدقائق (مثلاً: موعد مع الطبيب 30):")
        context.user_data["action"] = "add_reminder"

    elif query.data == "view_reminders":
        if chat_id in reminders and reminders[chat_id]:
            reminders_text = "\n".join(
                [f"{r['description']} - {r['time']}" for r in reminders[chat_id]]
            )
            await query.edit_message_text(f"تذكيراتك السابقة:\n{reminders_text}")
        else:
            await query.edit_message_text("لا توجد تذكيرات محفوظة.")

# التعامل مع إدخالات المستخدم
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name  # الحصول على اسم المستخدم
    user_text = update.message.text
    print(f"User {chat_id} sent a message: {user_text}")

    if "action" in context.user_data:
        if context.user_data["action"] == "add_note":
            # إضافة الملاحظة
            if chat_id not in notes:
                notes[chat_id] = []
            notes[chat_id].append(user_text)
            print(f"Added note for user {chat_id}: {user_text}")
            await update.message.reply_text(f"تم إضافة الملاحظة: {user_text}")
            del context.user_data["action"]

        elif context.user_data["action"] == "add_reminder":
            try:
                description, minutes = user_text.rsplit(" ", 1)
                minutes = int(minutes)
                reminder_time = datetime.now() + timedelta(minutes=minutes)
                if chat_id not in reminders:
                    reminders[chat_id] = []
                reminders[chat_id].append({"description": description, "time": reminder_time})
                print(f"Added reminder for user {chat_id}: {description} in {minutes} minutes")

                # إرسال تأكيد
                await update.message.reply_text(f"تم إضافة التذكرة: {description} بعد {minutes} دقيقة.")
                del context.user_data["action"]

                # جدولة التذكير
                asyncio.create_task(send_reminder(context, chat_id, user_name, description, reminder_time))
            except ValueError:
                await update.message.reply_text("يرجى كتابة التذكرة مع الوقت بالدقائق بشكل صحيح (مثلاً: موعد مع الطبيب 30).")

# إرسال التذكير
async def send_reminder(context, chat_id, user_name, description, reminder_time):
    await asyncio.sleep((reminder_time - datetime.now()).total_seconds())
    print(f"Sending reminder to user {chat_id}: {description}")
    await context.bot.send_message(chat_id, f"مرحبًا {user_name}، تذكير: {description}")

# إعداد البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is running...")
    app.run_polling()
