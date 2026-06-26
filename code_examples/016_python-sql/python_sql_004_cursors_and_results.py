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

with psycopg.connect(conn_string) as conn:
    with conn.cursor(row_factory=dict_row) as cursor:
        # --- DML: INSERT a record ---
        cursor.execute("""
            INSERT INTO examples.employees (emp_id, emp_name, emp_title, emp_salary)
            VALUES (1011, 'Alice', 'Engineering', 85000.00)
        """)

        # --- DML: SELECT with fetchone() ---
        # Useful when expecting a single result, such as a lookup by primary key
        cursor.execute("""SELECT emp_id, emp_name, emp_title, emp_salary 
                       FROM examples.employees WHERE emp_id = 1011
                       """)
        row = cursor.fetchone()
        print("::: " * 5)
        print("::: fetchone() :::")
        print("::: " * 5)
        if row:
            print(row["emp_id"], row["emp_name"], row["emp_title"], row["emp_salary"])

        # --- DML: SELECT with fetchall() ---
        # Retrieves all remaining rows — use with care on large result sets
        cursor.execute("SELECT * FROM examples.employees")
        rows = cursor.fetchall()
        print("::: " * 5)
        print("::: fetchall() :::")
        print("::: " * 5)
        for r in rows:
            print(r["emp_id"], r["emp_name"], r["emp_title"], r["emp_salary"])

        # --- DML: UPDATE a record ---        
        cursor.execute("""
            UPDATE examples.employees SET emp_salary = 99999 WHERE emp_id = 1011
        """)

        # --- DML: SELECT with fetchmany() ---
        # Retrieves a specific number of rows at a time
        # If fewer rows remain than requested, only the remaining rows are returned
        cursor.execute("SELECT * FROM examples.employees")
        batch = cursor.fetchmany(15)
        print("::: " * 5)
        print("::: fetchmany() :::")
        print("::: " * 5)
        for r in batch:
            print(r["emp_id"], r["emp_name"], r["emp_title"], r["emp_salary"])


        # --- DML: DELETE a record ---
        cursor.execute("DELETE FROM examples.employees WHERE emp_id = 1011")

# Transaction is committed automatically when the 'with' block exits cleanly
# If an exception is raised inside the block, it is rolled back automatically


# --- Manual commit/rollback with try/except (illustrative purposes only) ---
# This block mirrors what the Connection context manager does automatically.
# It is shown here to illustrate what is happening under the hood —
# always prefer using a Connection as a context manager in practice (as shown above).
conn = psycopg.connect(conn_string)
cursor = conn.cursor(row_factory=dict_row)

try:
    # Attempt to execute a SQL statement
    cursor.execute("""
        INSERT INTO examples.employees VALUES (1012, 'Bob', 'Marketing Lead', 72000.00)
    """)
except Exception as e:
    # If anything goes wrong, roll back all uncommitted changes
    # This prevents partial or corrupt data from being written to the database
    conn.rollback()
    print(f"Transaction failed, rolling back: {e}")
else:
    # If no exception was raised, commit the transaction to apply changes permanently
    conn.commit()
finally:
    # Always runs regardless of success or failure —
    # ensures the cursor and connection are closed and resources are released
    cursor.close()
    conn.close()