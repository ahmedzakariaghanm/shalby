import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from datetime import datetime, timedelta
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# قائمة لتخزين التذكيرات
reminders = {}
user_data = {}

# دالة لبدء إضافة تذكير
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_data[chat_id] = {}

    # إرسال رسالة ترحيبية وشرح كيف يعمل البوت
    welcome_message = (
        f"مرحبًا بك {update.message.from_user.first_name} في بوت التذكيرات! 🎉\n\n"
        "سأساعدك في إضافة تذكير جديد. في البداية، سأطلب منك اختيار التاريخ والوقت.\n"
        "الآن، دعني أعرف التاريخ الذي ترغب في إضافة التذكير فيه."
    )
    await update.message.reply_text(welcome_message)

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

        # طلب من المستخدم كتابة الملاحظة
        await query.edit_message_text("الآن، يرجى كتابة وصف التذكير (مثل: موعد مع الطبيب)")

    elif query.message.text and chat_id in user_data and 'time' in user_data[chat_id]:
        # حفظ التذكير بعد كتابة الوصف
        description = query.message.text
        date_time_str = f"{user_data[chat_id]['date']} {user_data[chat_id]['time']}"
        reminder_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")

        # حفظ التذكير في القائمة
        reminders[chat_id] = {"time": reminder_time, "description": description}
        await query.edit_message_text(f"تم إضافة التذكير: {description} في {reminder_time}")

        # تنظيف بيانات المستخدم
        user_data.pop(chat_id, None)

# التعامل مع رسائل المستخدمين عند فتح الشات
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # التأكد من وجود chat_id في user_data
    if chat_id not in user_data:
        user_data[chat_id] = {}  # إضافة entry جديد للمستخدم

    # التحقق مما إذا كانت آخر رسالة للمستخدم هي رسالة ترحيب
    if user_data[chat_id].get('last_message') != 'welcome':
        welcome_message = f"مرحبًا بك {update.message.from_user.first_name} في بوت التذكيرات! 🎉\n\n" \
                          "سأساعدك في إضافة تذكير جديد. في البداية، سأطلب منك اختيار التاريخ والوقت.\n" \
                          "الآن، دعني أعرف التاريخ الذي ترغب في إضافة التذكير فيه."
        await update.message.reply_text(welcome_message)

        # تخزين حالة الرسالة الترحيبية
        user_data[chat_id]['last_message'] = 'welcome'

        # عرض الخيارات للمستخدم
        options_keyboard = [
            [InlineKeyboardButton("إضافة ملاحظة جديدة", callback_data="add_note")],
            [InlineKeyboardButton("عرض الملاحظات السابقة", callback_data="show_notes")],
            [InlineKeyboardButton("إضافة تذكير جديد", callback_data="add_reminder")],
            [InlineKeyboardButton("عرض التذكيرات السابقة", callback_data="show_reminders")]
        ]

        reply_markup = InlineKeyboardMarkup(options_keyboard)
        await update.message.reply_text("ماذا ترغب في فعله؟", reply_markup=reply_markup)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر وإعدادات
    app.add_handler(CommandHandler("start", welcome_user))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()
