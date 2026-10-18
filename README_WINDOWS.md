# Princess Eagle Booking — Windows

ضع كل الملفات كما هي في نفس المجلد، ولا تشغّل `app.py` وحده من مكان آخر.

## تشغيل سريع
1. ثبّت Python 3.11 أو أحدث.
2. شغّل `run_windows.bat` بالنقر المزدوج.
3. افتح http://127.0.0.1:5000

## تشغيل يدوي
```bat
cd مسار-المجلد
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

صفحة الأدمن: http://127.0.0.1:5000/admin
مفتاح التجربة: `princess-admin`

مهم: يجب أن يبقى هذا الهيكل موجودًا:
```text
app.py
requirements.txt
templates\index.html
templates\admin.html
static\css\style.css
static\js\app.js
static\js\admin.js
static\assets\...
```
