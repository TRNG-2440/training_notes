import psycopg
import os
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

conn_string = (
    f"host={os.environ.get('DB_HOST')} "
    f"dbname={os.environ.get('DB_NAME')} "
    f"user={os.environ.get('DB_USER')} "
    f"password={os.environ.get('DB_PASSWORD')} "
    f"port={os.environ.get('DB_PORT')}"
)

# --- Preferred pattern: nested context managers ---
# The outer 'with' manages the connection:
#   - commits the transaction if the block completes successfully
#   - rolls back the transaction if an exception is raised
#   - closes the connection when the block exits
#
# The inner 'with' manages the cursor:
#   - closes the cursor when the block exits
#
# row_factory=dict_row is passed to conn.cursor() to enable
# column name access on returned rows (e.g. row["name"])
with psycopg.connect(conn_string) as conn:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT emp_id, name FROM examples.employees")
        rows = cursor.fetchall()
        for row in rows:
            print(row["emp_id"], row["emp_name"])

# Both the cursor and connection are automatically closed here
# No need to call cursor.close() or conn.close() manually


# --- What happens without a context manager (avoid this pattern) ---
conn = psycopg.connect(conn_string)
cursor = conn.cursor(row_factory=dict_row)

cursor.execute("SELECT emp_id, name FROM examples.employees")
rows = cursor.fetchall()

for row in rows:
    print(row["emp_id"], row["emp_name"])

# If an exception occurs above, these lines are never reached
# and the connection remains open
cursor.close()
conn.close()