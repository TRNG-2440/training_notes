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

# --- SQL Injection: what it looks like and why it is dangerous ---
malicious_input = "'' OR '1'='1'"

# NEVER do this — vulnerable to SQL injection
query = f"SELECT * FROM users WHERE username = '{malicious_input}'"
# Resulting SQL: SELECT * FROM users WHERE username = '' OR '1'='1'
# '1'='1' is always true, so this query returns every row in the table


# --- Parameterized queries: the correct approach ---
with psycopg.connect(conn_string) as conn:
    with conn.cursor(row_factory=dict_row) as cursor:

        # SELECT with a parameterized WHERE clause
        username = "joseph"

        # we use the 'lower' function to make the input case-insensitive
        cursor.execute(
            "SELECT emp_id, emp_name FROM examples.employees WHERE lower(emp_name) = %s",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            print(row["emp_id"], row["emp_name"])

        # INSERT with multiple parameterized values
        cursor.execute(
            "INSERT INTO examples.employees (emp_id, emp_name, emp_title, emp_salary) VALUES (%s, %s, %s, %s)",
            (1013, "Kara", "Data Engineer", 88000.00)
        )

        # UPDATE with parameterized values
        cursor.execute(
            "UPDATE examples.employees SET emp_salary = %s WHERE emp_id = %s",
            (92000.00, 1013)
        )

        # DELETE with a parameterized WHERE clause
        cursor.execute(
            "DELETE FROM examples.employees WHERE emp_id = %s",
            (1,) # recall - a single-value tuple is created using a comma
        )


# --- Common mistakes that can reintroduce SQL injection risk ---
# NEVER use f-strings to embed values in a query
# cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")  # WRONG

# NEVER use .format() to embed values in a query
# cursor.execute("SELECT * FROM users WHERE username = '{}'".format(username))  # WRONG

# NEVER use string concatenation to embed values in a query
# cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")  # WRONG