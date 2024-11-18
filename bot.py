import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# قائمة لتخزين التذكيرات والملاحظات
reminders = {}
notes = {}
user_data = {}

# قائمة لتخزين آخر رسالة مرسلة لكل مستخدم
last_message = {}

# دالة لبدء التفاعل مع البوت (رسالة ترحيب)
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name

    # التحقق إذا كانت آخر رسالة هي رسالة ترحيب
    if chat_id in last_message and last_message[chat_id] == 'welcome':
        return  # لا تفعل شيئًا إذا كانت آخر رسالة ترحيب

    # إرسال رسالة ترحيب جديدة
    welcome_message = f"مرحبًا {user_name}! 🎉\nأنا هنا لمساعدتك. ماذا تحتاج؟"
    await update.message.reply_text(welcome_message)

    # تخزين نوع الرسالة المرسلة (ترحيب)
    last_message[chat_id] = 'welcome'

    # عرض الاختيارات للمستخدم
    keyboard = [
        [InlineKeyboardButton("إضافة ملاحظة جديدة", callback_data="add_note")],
        [InlineKeyboardButton("عرض الملاحظات السابقة", callback_data="view_notes")],
        [InlineKeyboardButton("إضافة تذكير جديد", callback_data="add_reminder")],
        [InlineKeyboardButton("عرض التذكيرات السابقة", callback_data="view_reminders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختار ما تريد:", reply_markup=reply_markup)

# دالة لإضافة ملاحظة جديدة
async def add_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat_id
    await update.callback_query.edit_message_text("يرجى كتابة الملاحظة الآن.")
    user_data[chat_id] = {'action': 'add_note'}

# دالة لعرض الملاحظات السابقة
async def view_notes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat_id
    if chat_id in notes and notes[chat_id]:
        notes_message = "\n".join(notes[chat_id])
    else:
        notes_message = "لا توجد ملاحظات سابقة."
    await update.callback_query.edit_message_text(f"الملاحظات السابقة:\n{notes_message}")

# دالة لإضافة تذكير جديد
async def add_reminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat_id
    user_data[chat_id] = {'action': 'add_reminder'}

    # طلب التاريخ
    today = datetime.now()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=f"date:{(today + timedelta(days=i)).strftime('%Y-%m-%d')}")] for i in range(7)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("اختر التاريخ:", reply_markup=reply_markup)

# دالة لعرض التذكيرات السابقة
async def view_reminders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.callback_query.message.chat_id
    if chat_id in reminders and reminders[chat_id]:
        reminders_message = "\n".join([f"{reminder['description']} في {reminder['time']}" for reminder in reminders[chat_id]])
    else:
        reminders_message = "لا توجد تذكيرات سابقة."
    await update.callback_query.edit_message_text(f"التذكيرات السابقة:\n{reminders_message}")

# التعامل مع الردود من الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id

    # التعامل مع اختيار التاريخ
    if query.data.startswith("date:"):
        selected_date = query.data.split(":")[1]
        user_data[chat_id]['date'] = selected_date

        # عرض أزرار لاختيار الوقت
        keyboard = [InlineKeyboardButton(f"{hour}:00", callback_data=f"time:{hour}:00") for hour in range(9, 21)]
        reply_markup = InlineKeyboardMarkup([keyboard])
        await query.edit_message_text("اختر الوقت:", reply_markup=reply_markup)

    # التعامل مع اختيار الوقت
    elif query.data.startswith("time:"):
        selected_time = query.data.split(":")[1]
        user_data[chat_id]['time'] = selected_time

        # طلب من المستخدم كتابة وصف التذكير
        await query.edit_message_text("الآن، يرجى كتابة وصف التذكير (مثل: موعد مع الطبيب)")

    # حفظ التذكير بعد كتابة الوصف
    elif query.message.text and chat_id in user_data and 'time' in user_data[chat_id]:
        description = query.message.text
        date_time_str = f"{user_data[chat_id]['date']} {user_data[chat_id]['time']}"
        reminder_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")

        # حفظ التذكير في القائمة
        if chat_id not in reminders:
            reminders[chat_id] = []
        reminders[chat_id].append({"time": reminder_time, "description": description})
        await query.edit_message_text(f"تم إضافة التذكير: {description} في {reminder_time}")

        # تنظيف بيانات المستخدم
        user_data.pop(chat_id, None)

    # حفظ الملاحظة
    elif query.message.text and chat_id in user_data and user_data[chat_id]['action'] == 'add_note':
        description = query.message.text
        if chat_id not in notes:
            notes[chat_id] = []
        notes[chat_id].append(description)
        await query.edit_message_text(f"تم إضافة الملاحظة: {description}")
        user_data.pop(chat_id, None)

# تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة أوامر وإعدادات البوت
    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^date:|^time:"))
    app.add_handler(CallbackQueryHandler(add_note_handler, pattern="^add_note$"))
    app.add_handler(CallbackQueryHandler(view_notes_handler, pattern="^view_notes$"))
    app.add_handler(CallbackQueryHandler(add_reminder_handler, pattern="^add_reminder$"))
    app.add_handler(CallbackQueryHandler(view_reminders_handler, pattern="^view_reminders$"))

    # بدء تشغيل البوت
    print("Bot is running...")
    app.run_polling()
