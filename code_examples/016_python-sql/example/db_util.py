# =============================================================================
# Database Utility Module
# This module provides a utility method to be called by dao which is used to
# decouple database credentials from dao implementation further. In theory
# we can now completely change the method in which database credentials are
# read, without touching the dao CRUD operation functions
# =============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

def get_conn_string() -> str:
    return (
        f"host={os.environ.get('DB_HOST')} "
        f"dbname={os.environ.get('DB_NAME')} "
        f"user={os.environ.get('DB_USER')} "
        f"password={os.environ.get('DB_PASSWORD')} "
        f"port={os.environ.get('DB_PORT')}"
    )