from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('smm_database.db')
    c = conn.cursor()
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL,
        platform TEXT NOT NULL,
        target_url TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        progress INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Services table
    c.execute('''CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        price_per_1000 REAL DEFAULT 0.00,
        min_quantity INTEGER DEFAULT 10,
        max_quantity INTEGER DEFAULT 10000
    )''')
    
    # Insert default services if table is empty
    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        services = [
            ('Instagram Followers', 'Instagram', 0.00, 10, 10000),
            ('Instagram Likes', 'Instagram', 0.00, 10, 5000),
            ('Instagram Views', 'Instagram', 0.00, 100, 50000),
            ('TikTok Followers', 'TikTok', 0.00, 10, 10000),
            ('TikTok Likes', 'TikTok', 0.00, 10, 5000),
            ('TikTok Views', 'TikTok', 0.00, 100, 100000),
            ('Telegram Members', 'Telegram', 0.00, 10, 5000),
            ('Telegram Views', 'Telegram', 0.00, 100, 50000)
        ]
        c.executemany('INSERT INTO services (name, platform, price_per_1000, min_quantity, max_quantity) VALUES (?, ?, ?, ?, ?)', services)
    
    conn.commit()
    conn.close()

# Background worker to process orders
def process_orders():
    while True:
        try:
            conn = sqlite3.connect('smm_database.db')
            c = conn.cursor()
            
            # Get pending orders
            c.execute('SELECT * FROM orders WHERE status = "pending"')
            orders = c.fetchall()
            
            for order in orders:
                order_id, service_type, platform, target_url, quantity, status, progress, created_at = order
                
                # Simulate processing
                c.execute('UPDATE orders SET status = "processing" WHERE id = ?', (order_id,))
                conn.commit()
                
                # Simulate gradual progress
                for i in range(0, 101, random.randint(5, 15)):
                    time.sleep(random.uniform(0.5, 2.0))
                    c.execute('UPDATE orders SET progress = ? WHERE id = ?', (min(i, 100), order_id))
                    conn.commit()
                
                # Mark as completed
                c.execute('UPDATE orders SET status = "completed", progress = 100 WHERE id = ?', (order_id,))
                conn.commit()
                
            conn.close()
            time.sleep(5)
            
        except Exception as e:
            print(f"Background worker error: {e}")
            time.sleep(10)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    conn = sqlite3.connect('smm_database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM services')
    services = c.fetchall()
    conn.close()
    return render_template('services.html', services=services)

@app.route('/order', methods=['POST'])
def create_order():
    data = request.get_json()
    
    service_id = data.get('service_id')
    target_url = data.get('target_url')
    quantity = int(data.get('quantity', 0))
    
    if not target_url or quantity <= 0:
        return jsonify({'error': 'Invalid input'}), 400
    
    conn = sqlite3.connect('smm_database.db')
    c = conn.cursor()
    
    # Get service info
    c.execute('SELECT name, platform FROM services WHERE id = ?', (service_id,))
    service = c.fetchone()
    
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    service_name, platform = service
    
    # Create order
    c.execute('''INSERT INTO orders (service_type, platform, target_url, quantity) 
                 VALUES (?, ?, ?, ?)''', (service_name, platform, target_url, quantity))
    
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'order_id': order_id, 'message': 'Order created successfully'})

@app.route('/orders')
def view_orders():
    conn = sqlite3.connect('smm_database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/api/order/<int:order_id>')
def get_order_status(order_id):
    conn = sqlite3.connect('smm_database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    conn.close()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'id': order[0],
        'service_type': order[1],
        'platform': order[2],
        'target_url': order[3],
        'quantity': order[4],
        'status': order[5],
        'progress': order[6],
        'created_at': order[7]
    })

if __name__ == '__main__':
    init_db()
    
    # Start background worker
    worker_thread = threading.Thread(target=process_orders, daemon=True)
    worker_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
