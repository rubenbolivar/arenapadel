import os
import psycopg2

db_params = {
    'dbname': os.getenv('DB_NAME', 'arenapadel'),
    'user': os.getenv('DB_USER', 'arenapadel'),
    'password': os.getenv('DB_PASSWORD', 'ArenaPadel2025!'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': os.getenv('DB_PORT', '5432')
}

print("DB Parameters:", db_params)

try:
    conn = psycopg2.connect(**db_params)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print("Error:", str(e))
