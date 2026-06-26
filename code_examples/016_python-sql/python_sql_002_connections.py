import psycopg
import os
from dotenv import load_dotenv, dotenv_values
from psycopg.rows import dict_row

# --- .env file contents (never commit this file) ---
# DB_HOST=host_name
# DB_NAME=database_name
# DB_USER=database_user_name
# DB_PASSWORD=password_value
# DB_PORT=5432

# Load .env file values into the process environment
load_dotenv()


# --- Method 1: Keyword arguments with os.environ.get() (recommended) ---
# load_dotenv() above makes .env values available as environment variables,
# so os.environ.get() can read them — the same way it would read variables
# set directly at the OS level. This means this pattern works identically
# whether credentials come from a .env file or are configured on the host machine.
conn = psycopg.connect(
    host=os.environ.get("DB_HOST"),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    port=os.environ.get("DB_PORT"),
    row_factory=dict_row
)
conn.close()


# --- Method 2: Keyword arguments with dotenv_values() dictionary ---
# dotenv_values() reads the .env file directly into a Python dictionary
# without loading values into the process environment.
# Useful when you want to keep credentials isolated from the environment,
# but is specific to .env files and does not work with OS-level variables.
config = dotenv_values()

conn = psycopg.connect(
    host=config["DB_HOST"],
    dbname=config["DB_NAME"],
    user=config["DB_USER"],
    password=config["DB_PASSWORD"],
    port=config["DB_PORT"],
    row_factory=dict_row
)
conn.close()


# --- Method 3: Connection string with hardcoded values (never do this) ---
# Credentials are embedded directly in the source code.
# This is a serious security risk — never commit hardcoded credentials
# to version control or share code written this way.
conn = psycopg.connect(
    "host=localhost dbname=example user=postgres password=secretpass port=5432"
)
conn.close()