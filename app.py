from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3, os
from datetime import datetime, date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'princess_eagle.db')
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change-this-secret')
ADMIN_KEY = os.environ.get('PRINCESS_ADMIN_KEY', 'princess-admin')

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, duration INTEGER NOT NULL, price REAL NOT NULL, active INTEGER DEFAULT 1, image TEXT);
    CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, phone TEXT NOT NULL, service_id INTEGER NOT NULL, barber TEXT NOT NULL, booking_date TEXT NOT NULL, booking_time TEXT NOT NULL, status TEXT DEFAULT 'confirmed', created_at TEXT NOT NULL, FOREIGN KEY(service_id) REFERENCES services(id), UNIQUE(booking_date, booking_time, barber));
    ''')
    if conn.execute('SELECT COUNT(*) FROM settings').fetchone()[0] == 0:
        conn.executemany('INSERT INTO settings(key,value) VALUES (?,?)', [('weekly_title','Textured Fade'),('weekly_price','8'),('weekly_image','haircut_reference.jpeg')])
    if conn.execute('SELECT COUNT(*) FROM services').fetchone()[0] == 0:
        conn.executemany('INSERT INTO services(name,description,duration,price,image) VALUES (?,?,?,?,?)', [
            ('قص شعر كلاسيكي','قصة وتسريح احترافي',30,5,'haircut_reference.jpeg'), ('قص شعر + لحية','قص وتحديد دقيق',45,8,'haircut_reference.jpeg'), ('Royal Experience','عناية كاملة للشعر واللحية',90,18,'haircut_reference.jpeg')])
    conn.commit(); conn.close()

def settings():
    return {r['key']: r['value'] for r in db().execute('SELECT key,value FROM settings')}

@app.route('/')
def home():
    conn=db(); services=[dict(r) for r in conn.execute('SELECT * FROM services WHERE active=1')]; conn.close()
    return render_template('index.html', services=services, settings=settings())

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('key') == ADMIN_KEY: session['admin'] = True
        else: return render_template('admin.html', locked=True)
    if not session.get('admin'): return render_template('admin.html', locked=True)
    conn=db(); rows=conn.execute('''SELECT b.*, s.name service_name FROM bookings b JOIN services s ON s.id=b.service_id ORDER BY booking_date,booking_time''').fetchall(); services=conn.execute('SELECT * FROM services ORDER BY active DESC,id').fetchall(); conn.close()
    return render_template('admin.html', locked=False, bookings=[dict(r) for r in rows], services=[dict(r) for r in services], settings=settings())

@app.post('/api/bookings')
def create_booking():
    data=request.get_json(force=True); required=['customer_name','phone','service_id','barber','booking_date','booking_time']
    if any(not data.get(k) for k in required): return jsonify(error='يرجى تعبئة جميع الحقول'),400
    conn=db()
    try:
        conn.execute('INSERT INTO bookings(customer_name,phone,service_id,barber,booking_date,booking_time,created_at) VALUES (?,?,?,?,?,?,?)', (data['customer_name'],data['phone'],int(data['service_id']),data['barber'],data['booking_date'],data['booking_time'],datetime.now().isoformat(timespec='seconds'))); conn.commit()
    except sqlite3.IntegrityError: conn.close(); return jsonify(error='هذا الموعد محجوز، اختر وقتًا آخر'),409
    conn.close(); return jsonify(ok=True,message='تم تأكيد حجزك بنجاح')

@app.get('/api/availability')
def availability():
    d=request.args.get('date',''); barber=request.args.get('barber','يوسف'); conn=db(); rows=conn.execute('SELECT booking_time FROM bookings WHERE booking_date=? AND barber=? AND status!=\'cancelled\'',(d,barber)).fetchall(); conn.close(); return jsonify(booked=[r['booking_time'] for r in rows])

@app.post('/api/admin/weekly')
def update_weekly():
    if not session.get('admin'): return jsonify(error='غير مصرح'),401
    data=request.get_json(force=True); conn=db()
    for key in ('weekly_title','weekly_price','weekly_image'):
        if key in data: conn.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(data[key])))
    conn.commit(); conn.close(); return jsonify(ok=True, settings=settings())

@app.post('/api/admin/services/<int:sid>')
def update_service(sid):
    if not session.get('admin'): return jsonify(error='غير مصرح'),401
    data=request.get_json(force=True); conn=db(); conn.execute('UPDATE services SET name=?, price=?, active=? WHERE id=?',(data.get('name'),float(data.get('price',0)),int(bool(data.get('active',True))),sid)); conn.commit(); conn.close(); return jsonify(ok=True)

@app.post('/api/admin/bookings/<int:bid>/status')
def booking_status(bid):
    if not session.get('admin'): return jsonify(error='غير مصرح'),401
    status=request.get_json(force=True).get('status','confirmed'); conn=db(); conn.execute('UPDATE bookings SET status=? WHERE id=?',(status,bid)); conn.commit(); conn.close(); return jsonify(ok=True)

if __name__ == '__main__':
    init_db(); app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)
