import psycopg
from psycopg.rows import dict_row
from dataclasses import dataclass
from typing import Optional
from db_util import get_conn_string


# =============================================================================
# DATA ACCESS OBJECT (DAO) PATTERN
#
# A DAO is a design pattern that encapsulates all database interaction for a
# specific table or entity into a single class. The rest of the application
# calls methods on the DAO and receives Python objects back — it never writes
# SQL directly or handles raw database results.
#
# This separation provides two key benefits:
#   1. Single responsibility — all SQL for the employees table lives here.
#      If the schema changes, this file is the only place that needs updating.
#   2. Decoupling — the API layer, business logic, and any other part of the
#      application have no knowledge of psycopg3, SQL, or the database schema.
#      They work exclusively with EmployeeRecord dataclass instances.
#
# Our DAO is intentionally unaware of other libraries (like FastAPI, Pydantic,
# pandas, etc...) - decoupling database communication from other concerns
# =============================================================================


# =============================================================================
# DATABASE MODEL
#
# EmployeeRecord represents a single row from the examples.employees table. 
# Field names mirror the column names to allow for clean mapping between 
# Python objects/responses/etc and SQL table schema
#
# @dataclass is used rather than Pydantic BaseModel because data reaching
# this layer has already been validated — first by Pydantic at the API layer,
# and again by PostgreSQL at the schema level. Runtime validation here would
# be redundant overhead.
# =============================================================================
@dataclass
class EmployeeRecord:
    emp_id: int
    emp_name: str
    emp_title: str
    emp_salary: float


# =============================================================================
# DAO CLASS
# =============================================================================
class EmployeeDAO:
    def __init__(self):
        # Connection string is built once at instantiation from environment
        # variables loaded by db_util. All methods reuse this value.
        self.conn_string = get_conn_string()

    def _map_row(self, row) -> EmployeeRecord:
        # Private helper that converts a psycopg Row (dict-style) into an
        # EmployeeRecord dataclass instance. Every method that fetches rows
        # routes through here, so any column name change only needs updating
        # in this one place rather than across every query method.
        return EmployeeRecord(
            emp_id=row["emp_id"],
            emp_name=row["emp_name"],
            emp_title=row["emp_title"],
            emp_salary=row["emp_salary"]
        )

    def get_all(self) -> list[EmployeeRecord]:
        # Retrieves every row from the employees table.
        # Returns an empty list if no records exist.
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT emp_id, emp_name, emp_title, emp_salary FROM examples.employees"
                )
                return [self._map_row(row) for row in cursor.fetchall()]

    def get_by_id(self, emp_id: int) -> Optional[EmployeeRecord]:
        # Retrieves a single employee by primary key.
        # Returns None if no record with the given emp_id exists —
        # the caller (endpoint handler) is responsible for raising a 404.
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT emp_id, emp_name, emp_title, emp_salary FROM examples.employees WHERE emp_id = %s",
                    (emp_id,)
                )
                row = cursor.fetchone()
                return self._map_row(row) if row else None

    def create(self, record: EmployeeRecord) -> EmployeeRecord:
        # Inserts a new employee record into the database.
        # emp_id is excluded from the INSERT — PostgreSQL generates it automatically.
        # RETURNING emp_id retrieves the generated value immediately so it can be
        # included in the EmployeeRecord returned to the caller.
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO examples.employees (emp_name, emp_title, emp_salary)
                    VALUES (%s, %s, %s)
                    RETURNING emp_id
                    """,
                    (record.emp_name, record.emp_title, record.emp_salary)
                )
                new_id = cursor.fetchone()["emp_id"]
                return EmployeeRecord(
                    emp_id=new_id,
                    emp_name=record.emp_name,
                    emp_title=record.emp_title,
                    emp_salary=record.emp_salary
                )

    def update(self, record: EmployeeRecord) -> Optional[EmployeeRecord]:
        # Performs a full replacement of an existing employee record.
        # All fields are overwritten with the values provided in the record.
        # RETURNING retrieves the updated row directly — if nothing is returned,
        # no record with the given emp_id existed and None is returned to the caller.
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    UPDATE examples.employees
                    SET emp_name = %s, emp_title = %s, emp_salary = %s
                    WHERE emp_id = %s
                    RETURNING emp_id, emp_name, emp_title, emp_salary
                    """,
                    (record.emp_name, record.emp_title, record.emp_salary, record.emp_id)
                )
                row = cursor.fetchone()
                return self._map_row(row) if row else None

    def delete(self, emp_id: int) -> bool:
        # Deletes an employee record by primary key.
        # RETURNING emp_id is used to detect whether a row was actually deleted —
        # if fetchone() returns None, no record with the given emp_id existed.
        # Returns True if a record was deleted, False if no match was found.
        # The caller (endpoint handler) uses this to decide whether to raise a 404.
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "DELETE FROM examples.employees WHERE emp_id = %s RETURNING emp_id",
                    (emp_id,)
                )
                return cursor.fetchone() is not None