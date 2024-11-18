# استخدام صورة بايثون صغيرة الحجم
FROM python:3.10-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملف المتطلبات أولاً لتجنب إعادة تثبيت الحزم مع كل تعديل في الكود
COPY requirements.txt .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تنظيف الملفات المؤقتة لتقليل حجم الصورة النهائية
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# تحديد الأمر الذي سيعمل عند تشغيل الحاوية
CMD ["python", "bot.py"]
