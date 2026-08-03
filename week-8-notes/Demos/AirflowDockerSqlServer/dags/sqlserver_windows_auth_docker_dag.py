from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
from airflow.sdk import DAG, task


SQL_BRIDGE_BASE_URL = os.getenv(
    "SQL_BRIDGE_BASE_URL",
    "http://host.docker.internal:5055",
)


def call_bridge(endpoint: str) -> dict[str, Any]:
    """
    Call a predefined endpoint on the Windows SQL Server bridge.

    The bridge runs on Windows and connects to SQL Server using
    Windows Authentication.
    """

    base_url = SQL_BRIDGE_BASE_URL.rstrip("/")
    endpoint_path = endpoint.lstrip("/")
    url = f"{base_url}/{endpoint_path}"

    print(f"Calling SQL bridge: {url}")

    try:
        response = requests.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not communicate with the Windows SQL bridge.\n"
            f"URL: {url}\n\n"
            "Verify the following:\n"
            "1. start_sql_bridge.bat is running.\n"
            "2. http://localhost:5055/health works in Windows.\n"
            "3. Docker can reach host.docker.internal:5055.\n"
            "4. Windows Firewall allows TCP port 5055."
        ) from exc

    try:
        result = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "The SQL bridge did not return valid JSON.\n"
            f"HTTP status: {response.status_code}\n"
            f"Response body: {response.text}"
        ) from exc

    return result


with DAG(
    dag_id="sqlserver_windows_auth_docker_demo",
    description=(
        "Docker Airflow reads Windows SQL Server through "
        "a PowerShell Windows-authentication bridge"
    ),
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=[
        "docker",
        "sql-server",
        "windows-authentication",
    ],
) as dag:

    @task
    def test_connection() -> dict[str, Any]:
        """
        Verify that Docker Airflow can reach the Windows bridge
        and that the bridge can connect to SQL Server.
        """

        result = call_bridge("/health")

        print("=" * 70)
        print("SQL SERVER WINDOWS AUTHENTICATION TEST")
        print("=" * 70)
        print(f"Status       : {result.get('status')}")
        print(f"SQL login    : {result.get('login_name')}")
        print(f"Database     : {result.get('database')}")
        print(f"SQL Server   : {result.get('server_name')}")
        print(f"Windows user : {result.get('windows_user')}")

        if result.get("status") != "healthy":
            raise RuntimeError(
                f"The SQL bridge returned an unhealthy response: {result}"
            )

        return result

    @task
    def read_sales(
        connection_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Read sales rows from the Windows bridge.
        """

        print(
            "Connection test completed for:",
            connection_result.get("server_name"),
        )

        result = call_bridge("/sales")
        rows = result.get("data", [])

        print("=" * 70)
        print("SALES DATA RECEIVED FROM SQL SERVER")
        print("=" * 70)

        for row in rows:
            print(
                f"SaleID={row.get('SaleID')}, "
                f"Product={row.get('ProductName')}, "
                f"Category={row.get('Category')}, "
                f"Quantity={row.get('Quantity')}, "
                f"UnitPrice={row.get('UnitPrice')}, "
                f"SaleDate={row.get('SaleDate')}"
            )

        print(f"Total rows received: {len(rows)}")

        if not rows:
            raise RuntimeError(
                "The SQL bridge returned no rows from dbo.Sales."
            )

        return rows

    @task
    def calculate_summary(
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Calculate total quantity, total revenue,
        and category-wise revenue.
        """

        total_quantity = 0
        total_revenue = 0.0
        category_revenue: dict[str, float] = {}

        for row in rows:
            quantity = int(row["Quantity"])
            unit_price = float(row["UnitPrice"])
            category = str(row["Category"])

            revenue = quantity * unit_price

            total_quantity += quantity
            total_revenue += revenue

            category_revenue[category] = (
                category_revenue.get(category, 0.0) + revenue
            )

        summary = {
            "number_of_rows": len(rows),
            "total_quantity": total_quantity,
            "total_revenue": round(total_revenue, 2),
            "category_revenue": {
                category: round(revenue, 2)
                for category, revenue in category_revenue.items()
            },
        }

        print("=" * 70)
        print("SALES SUMMARY")
        print("=" * 70)
        print(f"Number of rows : {summary['number_of_rows']}")
        print(f"Total quantity : {summary['total_quantity']}")
        print(f"Total revenue  : {summary['total_revenue']:,.2f}")
        print("")
        print("Revenue by category:")

        for category, revenue in summary["category_revenue"].items():
            print(f"{category}: {revenue:,.2f}")

        return summary

    connection_details = test_connection()
    sales_rows = read_sales(connection_details)
    calculate_summary(sales_rows)