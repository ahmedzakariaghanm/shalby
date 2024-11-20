import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import time

LOCK_FILE = '/tmp/bot.lock'

if not (os.getenv("IS_PRIMARY_INSTANCE") == "true"):
    print("This is not the primary instance.")
    sys.exit()
else:
    if os.path.exists(LOCK_FILE):
        print("Bot is already running!")
        sys.exit()

# Create lock file
    with open(LOCK_FILE, 'w') as f:
        print("Bot locked!")
        f.write("locked")
        if os.path.exists(LOCK_FILE):
            print("yay")



# Check if lock file exists
# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# تخزين البيانات
reminders = {}
user_data = {}

# دالة لإرسال رسالة ترحيبية عند فتح الشات
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in user_data or user_data[chat_id].get("last_message") != "welcome":
        welcome_message = f"مرحبًا {update.message.from_user.first_name}! 🎉\nكيف يمكنني مساعدتك اليوم؟"
        await update.message.reply_text(welcome_message)

        user_data[chat_id] = {"last_message": "welcome", "notes": []}

        await show_options(update, context)

async def show_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = (
        update.message.chat_id if update.message
        else update.callback_query.message.chat.id
    )

    keyboard = []
    keyboard.append([InlineKeyboardButton("إضافة ملاحظة جديدة", callback_data="add_note")])
    if user_data[chat_id].get("notes"):
        keyboard.append([InlineKeyboardButton("عرض الملاحظات السابقة", callback_data="show_notes")])
    keyboard.append([InlineKeyboardButton("إضافة تذكير جديد", callback_data="add_reminder")])
    if chat_id in reminders:
        keyboard.append([InlineKeyboardButton("عرض التذكيرات السابقة", callback_data="show_reminders")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        print("reply_text")
        await update.message.reply_text("ماذا ترغب في فعله؟", reply_markup=reply_markup)
    else:
        print("edit_message_text")
        await update.callback_query.edit_message_text("؟ماذا ترغب في فعله؟", reply_markup=reply_markup)

# التعامل مع الأزرار التي يضغط عليها المستخدم
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من نوع التحديث
    if update.callback_query:
        query = update.callback_query
        print(f"Callback received: {query.data}")  # Add this line

        chat_id = query.message.chat.id  # استخدم chat.id لأننا نتعامل مع callback_query هنا

        if query.data == "add_note":
            # بداية إضافة ملاحظة جديدة
            user_data[chat_id]["adding_note"] = True
            await query.edit_message_text("أرسل لي النص الذي ترغب في حفظه كملاحظة.")
            # await save_note_handler(query,context)
        elif query.data == "show_notes":
            # عرض الملاحظات السابقة
            await show_notes_handler(update, context)

        elif query.data == "add_reminder":
            # بداية إضافة تذكير جديد
            await start_reminder(query.message, context, chat_id)

        elif query.data == "show_reminders":
            # عرض التذكيرات السابقة
            if chat_id in reminders:
                reminder = reminders[chat_id]
                await query.edit_message_text(f"التذكير: {reminder['description']} في {reminder['time']}")
            else:
                await query.edit_message_text("لا توجد تذكيرات سابقة.")
            await ask_for_more(query, context)
        elif query.data == "yes_more":
        # هنا نضيف debug للتأكد من استدعاء الدالة بشكل صحيح
            print("تم اختيار 'نعم'، سيتم عرض الخيارات")
        # بعد الضغط على "نعم"، يتم عرض الخيارات مرة أخرى
            await query.answer()  # للتأكيد على الرد
            await show_options(query, context)  # تمرير query بدلاً من message
        elif query.data == "no_more":
            await update.message.reply_text("شكرًا لاستخدامك البوت. نتمنى لك يومًا سعيدًا!")
    else:
        print("خطأ: لم يكن هناك callback_query.")

# دالة استقبال نص الملاحظة وحفظها
async def save_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("save_note_handler")
    if update.message:
        chat_id = update.message.chat.id  # استخدم chat.id لأننا نتعامل مع الرسائل هنا

        if user_data.get(chat_id, {}).get("adding_note"):
            note = update.message.text  # النص المرسل من المستخدم
            # إضافة الملاحظة للمستخدم
            user_data[chat_id]["notes"].append(note)
            # إيقاف وضع إضافة الملاحظة
            user_data[chat_id]["adding_note"] = False
            await update.message.reply_text("تم حفظ الملاحظة بنجاح.")
            await ask_for_more(update, context)
        else:
            await update.message.reply_text("أنت لست في وضع إضافة ملاحظة حاليًا.")
    else:
        print("خطأ: لم يكن هناك message.")



# عرض جميع الملاحظات
async def show_notes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id

    notes = user_data[chat_id].get("notes", [])
    if notes:
        notes_text = "\n".join(f"- {note}" for note in notes)
        await query.edit_message_text(f"الملاحظات السابقة:\n{notes_text}")
    else:
        await query.edit_message_text("لا توجد ملاحظات سابقة.")
    await ask_for_more(query, context)

# بدء إضافة تذكير جديد
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
    chat_id = chat_id or update.message.chat_id
    user_data[chat_id] = {}

    today = datetime.now()
    keyboard = [
        [InlineKeyboardButton((today + timedelta(days=i)).strftime("%Y-%m-%d"), callback_data=f"date:{i}")]
        for i in range(7)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر التاريخ:", reply_markup=reply_markup)

# دالة بدء إضافة ملاحظة جديدة
async def add_note_handler(message, context: ContextTypes.DEFAULT_TYPE):
    chat_id = message.message.chat.id  # استخدام message هنا لأنك تحصل على رسالة من query
    user_data[chat_id]["adding_note"] = True
    await message.message.reply_text("أرسل لي النص الذي ترغب في حفظه كملاحظة.")

# استفسار عن طلب إضافي
async def ask_for_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("نعم", callback_data="yes_more")],
        [InlineKeyboardButton("لا", callback_data="no_more")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("هل تحتاج شيئًا آخر؟", reply_markup=reply_markup)

# التعامل مع اختيار المستخدم بعد انتهاء المهمة
# async def ask_more_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()  # Acknowledge the callback

#     print("ask_more_handler")
#     print(update)
#     print(query)
    # elif query.data == "yes_more":
    #     # هنا نضيف debug للتأكد من استدعاء الدالة بشكل صحيح
    #     print("تم اختيار 'نعم'، سيتم عرض الخيارات")
    #     # بعد الضغط على "نعم"، يتم عرض الخيارات مرة أخرى
    #     await query.answer()  # للتأكيد على الرد
    #     await show_options(query, context)  # تمرير query بدلاً من message
    # elif query.data == "no_more":
    #     await update.message.reply_text("شكرًا لاستخدامك البوت. نتمنى لك يومًا سعيدًا!")

def start_bot():
    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # app.initialize()

        app.add_handler(CommandHandler('start', welcome_user))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_note_handler))
        # app.add_handler(CallbackQueryHandler(ask_more_handler, pattern="yes_more|no_more"))
        print(app.handlers)


        print("Bot is running...")

        # Start polling for updates
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        # Print the exception for debugging
        print(e)

if __name__ == "__main__":
    start_bot()
    # Cleanup: remove lock file when the bot stops
    os.remove(LOCK_FILE)

