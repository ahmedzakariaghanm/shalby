import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# قائمة لتخزين التذكيرات والملاحظات
reminders = {}
user_data = {}

# دالة لبدء إضافة تذكير
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data[chat_id] = {}

    # عرض الأزرار لاختيار التاريخ
    keyboard = []
    today = datetime.now()
    for i in range(7):  # عرض الأيام السبعة القادمة
        day = today + timedelta(days=i)
        keyboard.append([InlineKeyboardButton(day.strftime("%Y-%m-%d"), callback_data=f"date:{day.strftime('%Y-%m-%d')}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر التاريخ:", reply_markup=reply_markup)

# التعامل مع الردود من الأزرار التفاعلية
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id

    if query.data.startswith("date:"):
        # تخزين التاريخ المختار
        selected_date = query.data.split(":")[1]
        user_data[chat_id]['date'] = selected_date

        # عرض أزرار لاختيار الوقت
        keyboard = []
        for hour in range(9, 21):  # ساعات العمل بين 9 صباحًا و9 مساءً
            keyboard.append([InlineKeyboardButton(f"{hour}:00", callback_data=f"time:{hour}:00")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختر الوقت:", reply_markup=reply_markup)

    elif query.data.startswith("time:"):
        # تخزين الوقت المختار
        selected_time = query.data.split(":")[1]
        user_data[chat_id]['time'] = selected_time

        # طلب من المستخدم كتابة وصف التذكير
        await query.edit_message_text("الآن، يرجى كتابة وصف التذكير (مثل: موعد مع الطبيب)")

    elif query.data == "add_note":
        # طلب من المستخدم إرسال نص الملاحظة
        await query.edit_message_text("أرسل لي النص الذي ترغب في حفظه كملاحظة.")
        user_data[chat_id] = {"adding_note": True}

    elif query.data == "show_notes":
        # عرض الملاحظات السابقة
        notes = user_data.get(chat_id, {}).get("notes", [])
        if notes:
            await query.edit_message_text(f"الملاحظات السابقة: {', '.join(notes)}")
        else:
            await query.edit_message_text("لا توجد ملاحظات سابقة.")
        await ask_for_more(update, context)

    elif query.data == "show_reminders":
        # عرض التذكيرات السابقة
        if chat_id in reminders:
            reminder = reminders[chat_id]
            await query.edit_message_text(f"التذكير: {reminder['description']} في {reminder['time']}")
        else:
            await query.edit_message_text("لا توجد تذكيرات سابقة.")
        await ask_for_more(update, context)

# استقبال الرسائل النصية من المستخدم
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    if chat_id in user_data and user_data[chat_id].get("adding_note"):
        # إضافة الملاحظة إلى القائمة
        notes = user_data[chat_id].get("notes", [])
        notes.append(text)
        user_data[chat_id]["notes"] = notes

        # تأكيد الإضافة للمستخدم
        await update.message.reply_text(f"تم حفظ الملاحظة: {text}")
        user_data[chat_id]["adding_note"] = False

        # سؤال المستخدم إذا كان يحتاج إلى شيء آخر
        await ask_for_more(update, context)

# عرض الخيارات مرة أخرى
async def ask_for_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("إضافة ملاحظة جديدة", callback_data="add_note")],
        [InlineKeyboardButton("إضافة تذكير جديد", callback_data="add_reminder")]
    ]

    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id

    # إضافة خيارات عرض الملاحظات والتذكيرات إن وجدت
    if 'notes' in user_data.get(chat_id, {}):
        keyboard.insert(1, [InlineKeyboardButton("عرض الملاحظات السابقة", callback_data="show_notes")])
    if chat_id in reminders:
        keyboard.append([InlineKeyboardButton("عرض التذكيرات السابقة", callback_data="show_reminders")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, "هل تحتاج إلى شيء آخر؟", reply_markup=reply_markup)

# دالة لإرسال رسالة ترحيب للمستخدم عند فتح الشات
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # التحقق مما إذا كانت آخر رسالة للمستخدم هي رسالة ترحيب باستخدام المتغيرات المخزنة
    if chat_id not in user_data or user_data[chat_id].get('last_message', '') != 'welcome':
        welcome_message = f"مرحبًا بك {update.message.from_user.first_name} في بوت التذكيرات! 🎉\n\n" \
                          "سأساعدك في إضافة تذكير أو ملاحظة جديدة.\n"
        await update.message.reply_text(welcome_message)

        # تخزين حالة الرسالة الترحيبية
        user_data[chat_id] = {'last_message': 'welcome'}

        # عرض الخيارات للمستخدم
        await ask_for_more(update, context)

# دالة تبدأ البوت وتفحص حالة التشغيل
def start_bot():
    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # إضافة الأوامر وإعدادات الاستجابة
        app.add_handler(CommandHandler('start', welcome_user))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

        print("Bot is running...")
        app.run_polling(drop_pending_updates=True)  # استخدام polling مع التحقق من التعارض

    except Exception as e:
        print(f"Error starting the bot: {e}")

if __name__ == "__main__":
    start_bot()
