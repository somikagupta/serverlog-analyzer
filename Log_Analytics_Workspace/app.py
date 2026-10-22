
import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

LOG_PATTERN = re.compile(
    r'(\d+\.\d+\.\d+\.\d+).*?\[(.*?)\].*?"(?:GET|POST) .*?" (\d{3})'
)


# 1. Real-Time Tracker: Automatically generate a log entry whenever a page is accessed
@app.after_request
def track_real_users(response):
    ip = request.remote_addr
    now = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    method = request.method
    url = request.path
    status = response.status_code

    log_line = f'{ip} - - [{now}] "{method} {url} HTTP/1.1" {status} 1024\n'
    with open('server.log', 'a') as file:
        file.write(log_line)

    return response


# 2. Fake URLs for Testing
@app.route('/login')
def login_page():
    return "<h1>Login Page</h1> <p>User logged in successfully! (200 OK)</p>"


@app.route('/payment-crash')
def crash_page():
    return "<h1>Payment Failed!</h1> <p>Server Internal Error (500 Crash)</p>", 500


# 3. Database and Dashboard Logic
def setup_database():
    extracted_data = []

    with open('server.log', 'r') as file:
        for line in file:
            match = LOG_PATTERN.search(line)
            if match:
                extracted_data.append(
                    (match.group(1), match.group(2), int(match.group(3)))
                )

    conn = sqlite3.connect('server_logs.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            timestamp TEXT,
            status_code INTEGER
        )
    ''')

    cursor.execute('DELETE FROM logs')

    cursor.executemany(
        'INSERT INTO logs (ip_address, timestamp, status_code) VALUES (?, ?, ?)',
        extracted_data
    )

    conn.commit()
    conn.close()


def get_analytics():
    conn = sqlite3.connect('server_logs.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM logs WHERE status_code = 500")
    total_crashes = cursor.fetchone()[0]

    cursor.execute('''
        SELECT ip_address, COUNT(*) AS count
        FROM logs
        WHERE status_code = 500
        GROUP BY ip_address
        ORDER BY count DESC
        LIMIT 5
    ''')

    top_ips = cursor.fetchall()

    cursor.execute(
        "SELECT ip_address, timestamp, status_code FROM logs ORDER BY id DESC"
    )
    all_logs = cursor.fetchall()

    conn.close()

    return total_crashes, top_ips, all_logs


@app.route('/')
def dashboard():
    setup_database()
    total_crashes, top_ips, all_logs = get_analytics()

    return render_template(
        'index.html',
        crashes=total_crashes,
        top_ips=top_ips,
        logs=all_logs
    )


if __name__ == '__main__':
    app.run(debug=True)
