# استخدم صورة بايثون من Docker Hub
FROM python:3.10-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ الملفات المطلوبة من جهازك إلى الحاوية
COPY . /app

# تثبيت المكتبات المطلوبة من ملف requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# تعيين المتغيرات البيئية من ملف .env
ENV $(cat .env | xargs)

# تحديد الأمر الذي سيعمل عند تشغيل الحاوية
CMD ["python", "bot.py"]
