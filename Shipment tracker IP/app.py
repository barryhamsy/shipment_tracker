from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import os
import time

app = Flask(__name__)

# Function to calculate ETA
def calculate_eta(etd, destination):
    lead_times = {
        'Miri': 1,
        'Bintulu': 2,
        'Kuching': 7,
        'Sibu': 4,
        'Kota Kinabalu': 7,
        'Sandakan': 14,
        'Brunei': 5,
        'Labuan': 5,
        'Self Collect': 1
    }
    lead_time = timedelta(days=lead_times.get(destination, 0))
    return (datetime.strptime(etd, '%Y-%m-%d') + lead_time).strftime('%Y-%m-%d')

# SQLite database creation command
create_table_command = '''
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    so TEXT NOT NULL,
    dn TEXT NOT NULL,
    customer_name_and_address TEXT NOT NULL,
    phone TEXT NOT NULL,
    name TEXT NOT NULL,
    destination TEXT NOT NULL,
    etd DATE NOT NULL,
    eta DATE NOT NULL,
    logistic_partner TEXT NOT NULL,
    booking_date DATE NOT NULL,
    packing TEXT NOT NULL,
    chromascan TEXT NOT NULL,
    weight TEXT NOT NULL,
    volume TEXT NOT NULL,
    delivery_status TEXT NOT NULL
);
'''

# Execute the SQLite command
with sqlite3.connect('database.db') as conn:
    conn.execute(create_table_command)
    
# Route for the main page (shipment list without buttons)
@app.route('/shipment_list')
def shipment_list():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Order by the primary key (assuming it's an auto-incrementing ID) in descending order
    cursor.execute("SELECT * FROM shipments ORDER BY id DESC")
    
    shipments = cursor.fetchall()
    conn.close()
    return render_template('shipment_list.html', shipments=shipments)
    
# Route for the main page
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments ORDER BY id DESC")
    shipments = cursor.fetchall()
    conn.close()
    return render_template('index.html', shipments=shipments)

# Route to add a new shipment
@app.route('/add_shipment', methods=['POST'])
def add_shipment():
    so = request.form['so']
    dn = request.form['dn']
    customer_name_and_address = request.form['customer_name_and_address']
    phone = request.form['phone']
    name = request.form['name']
    destination = request.form['destination']
    etd = request.form['etd']
    logistic_partner = request.form['logistic_partner']
    booking_date = request.form['booking_date']
    packing = request.form['packing']
    chromascan = request.form['chromascan']
    weight = request.form['weight']
    volume = request.form['volume']
    delivery_status = request.form['delivery_status']

    eta = calculate_eta(etd, destination)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO shipments (so, dn, customer_name_and_address, phone, name, destination, etd, eta, logistic_partner, "
                   "booking_date, packing, chromascan, weight, volume, delivery_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (so, dn, customer_name_and_address, phone, name, destination, etd, eta, logistic_partner, booking_date, packing, chromascan, weight, volume, delivery_status))
    conn.commit()
    conn.close()

    return redirect(url_for('shipment_list'))

# Route to edit shipment
@app.route('/edit_shipment/<int:id>')
def edit_shipment(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments WHERE id=?", (id,))
    shipment = cursor.fetchone()
    conn.close()

    # Pass the calculate_eta function to the template
    return render_template('edit_shipment.html', shipment=shipment, calculate_eta=calculate_eta, id=id)

# Route to update shipment
@app.route('/update_shipment/<int:id>', methods=['POST'])
def update_shipment(id):
    so = request.form['so']
    dn = request.form['dn']
    customer_name_and_address = request.form['customer_name_and_address']
    phone = request.form['phone']
    name = request.form['name']
    etd = request.form['etd']
    packing = request.form['packing']
    chromascan = request.form['chromascan']
    weight = request.form['weight']
    volume = request.form['volume']
    logistic_partner = request.form['logistic_partner']
    delivery_status = request.form['delivery_status']
    destination = request.form['destination']
    booking_date = request.form['booking_date']
    eta = calculate_eta(etd,destination)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE shipments SET so=?, dn=?, customer_name_and_address=?, phone=?, name=?, destination=?, booking_date=?, etd=?, eta=?, packing=?, chromascan=?, weight=?, volume=?, logistic_partner=?, delivery_status=? WHERE id=?",
                   (so, dn, customer_name_and_address, phone, name,destination, booking_date, etd, eta, packing, chromascan, weight, volume, logistic_partner, delivery_status, id))
    conn.commit()
    conn.close()

    return redirect(url_for('shipment_list'))

# Route to delete a shipment
@app.route('/delete_shipment/<int:id>')
def delete_shipment(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shipments WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('shipment_list'))

@app.route('/search_shipment', methods=['POST'])
def search_shipment():
    search_term = request.form.get('search_term')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Updated SQL query to use LIKE for each column
    cursor.execute("""
        SELECT * FROM shipments
        WHERE so LIKE ? OR dn LIKE ? OR customer_name_and_address LIKE ? OR phone LIKE ?
        OR name LIKE ? OR destination LIKE ? OR etd LIKE ? OR eta LIKE ?
        OR logistic_partner LIKE ? OR booking_date LIKE ? 
        OR packing LIKE ? OR chromascan LIKE ? OR weight LIKE ? 
        OR volume LIKE ? OR delivery_status LIKE ?
    """, (f'%{search_term}%',) * 15)

    search_result = cursor.fetchall()
    conn.close()

    return render_template('shipment_list.html', shipments=search_result)

@app.route('/export_excel')
def export_excel():
    # Fetch data from the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments")
    data = cursor.fetchall()
    conn.close()

    # Create a Pandas DataFrame from the data
    df = pd.DataFrame(data, columns=[
        'id', 'so', 'dn', 'customer_name_and_address', 'phone', 'name', 'destination',
        'etd', 'eta', 'logistic_partner',
        'booking_date', 'packing', 'chromascan', 'weight', 'volume', 'delivery_status'
    ])

    # Save DataFrame to Excel file
    excel_filename = 'shipment_list.xlsx'
    df.to_excel(excel_filename, index=False)

    # Send the Excel file as a response
    return send_from_directory(os.getcwd(), excel_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
    while True:
        print("Keeping the terminal always on...")
        time.sleep(60)  # Sleep for 60 seconds