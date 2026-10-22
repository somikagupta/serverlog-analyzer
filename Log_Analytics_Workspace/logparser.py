
import re
import sqlite3

# Phase 1: Regex Pattern
LOG_PATTERN = re.compile(
    r'(\d+\.\d+\.\d+\.\d+).*?\[(.*?)\].*?"(?:GET|POST) .*?" (\d{3})'
)

def extract_data(file_path):
    cleaned_data = []
    with open(file_path, 'r') as file:
        for line in file:
            match = LOG_PATTERN.search(line)
            if match:
                ip = match.group(1)
                time = match.group(2)
                code = int(match.group(3))
                cleaned_data.append((ip, time, code))
    return cleaned_data


# Phase 2: Database Setup and Data Loading
def load_to_database(data):
    # Connect to the SQLite database (creates the file automatically if it does not exist)
    conn = sqlite3.connect('server_logs.db')
    cursor = conn.cursor()

    # Create a table to store the extracted data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            timestamp TEXT,
            status_code INTEGER
        )
    ''')

    # Delete old data to prevent duplicate entries when the script is run repeatedly
    cursor.execute('DELETE FROM logs')

    # Batch insertion: Insert all records from the tuple list in a single operation
    cursor.executemany('''
        INSERT INTO logs (ip_address, timestamp, status_code)
        VALUES (?, ?, ?)
    ''', data)

    conn.commit()  # Save the changes
    return conn


# Phase 3: SQL Analytics
def run_analytics(conn):
    cursor = conn.cursor()
    print("\n--- SERVER ANALYTICS REPORT ---")

    # SQL query: Identify which IP addresses generate the most 500 Internal Server Errors
    cursor.execute('''
        SELECT ip_address, COUNT(*) as error_count
        FROM logs
        WHERE status_code = 500
        GROUP BY ip_address
        ORDER BY error_count DESC
    ''')

    results = cursor.fetchall()

    print("\nTop IPs causing 500 Internal Server Errors:")
    for row in results:
        # row[0] contains the IP address, and row[1] contains the error count
        print(f"IP: {row[0]} | Crash Count: {row[1]}")

    conn.close()


# Main execution block
if __name__ == "__main__":
    print("1. Extracting data...")
    parsed_data = extract_data('server.log')

    print("2. Loading data into the database...")
    db_conn = load_to_database(parsed_data)

    print("3. Running SQL analytics...")
    run_analytics(db_conn)
