from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import threading
import time
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Keep-alive configuration
PING_INTERVAL = 840  # 14 minutes (less than Render's 15-minute limit)
APP_URL = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:8000')

def keep_alive():
    """Ping the application periodically to prevent it from sleeping"""
    while True:
        try:
            requests.get(APP_URL)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        time.sleep(PING_INTERVAL)

# Start keep-alive thread
if os.environ.get('RENDER') == 'true':
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()

# Add this dictionary for food images based on location/type
location_images = {
    'household': 'https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=500',
    'restaurant': 'https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=500',
    'default': 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=500'
}

db_file = "database.db"

def init_db():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS ngos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT, contact TEXT, location TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expiring_food (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            item_name TEXT, expiry_date TEXT, location TEXT, user_type TEXT)''')
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register_ngo', methods=['GET', 'POST'])
def register_ngo():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        location = request.form['location']
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ngos (name, contact, location) VALUES (?, ?, ?)",
                           (name, contact, location))
            conn.commit()
        return redirect(url_for('list_ngos'))
    return render_template('register_ngo.html')

@app.route('/list_ngos')
def list_ngos():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ngos")
        ngos = cursor.fetchall()
    return render_template('list_ngos.html', ngos=ngos)

@app.route('/find_ngos', methods=['GET', 'POST'])
def find_ngos():
    ngos = []
    if request.method == 'POST':
        location = request.form['location']
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ngos WHERE location=?", (location,))
            ngos = cursor.fetchall()
    return render_template('find_ngos.html', ngos=ngos)

@app.route('/add_expiring_food', methods=['GET', 'POST'])
def add_expiring_food():
    if request.method == 'POST':
        item_name = request.form['item_name']
        expiry_date = request.form['expiry_date']
        location = request.form['location']
        user_type = request.form['user_type']
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expiring_food (item_name, expiry_date, location, user_type) VALUES (?, ?, ?, ?)",
                           (item_name, expiry_date, location, user_type))
            conn.commit()
        return redirect(url_for('list_expiring_food'))
    return render_template('add_expiring_food.html')

@app.route('/list_expiring_food')
def list_expiring_food():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expiring_food")
        food_items = cursor.fetchall()
    return render_template('list_expiring_food.html', 
                         food_items=food_items, 
                         location_images=location_images)

@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
