"""
Create a databse from csv file in Database/customer_data.csv
"""

# Import modules
import sqlite3
import sys
from pathlib import Path
import pandas as pd


# ============================================================================
# Declare relative paths and table names
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 1. table
CSV_PATH_ORDERS = PROJECT_ROOT / "SQL_APP" / "Database" / "customer_data.csv"
TABLE_NAME_ORDERS = "customer_data"
# 2. table (relational)
CSV_PATH_SECRETS = PROJECT_ROOT / "SQL_APP" / "Database" / "customer_secrets.csv"
TABLE_NAME_SECRETS = "customer_secrets"
# Database path
DB_PATH = PROJECT_ROOT / "SQL_APP" / "Database" / "sql_playground.db"


# ============================================================================
# Build one database table from one CSV file
# ============================================================================
def build_database(csv_path: Path, table_name: str, conn) -> None:
    # Error log if csv file is missing
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    # Load dataframe and create more logs
    print(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Found columns: {list(df.columns)}")
    print(f"Number of rows: {len(df)}")
    df.to_sql(
        table_name,
        conn,
        index=False,
        if_exists="replace"
    )
    print(f"Table '{table_name}' created successfully.")


# ============================================================================
# Rebuild the complete database
# ============================================================================
def reset_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        build_database(
            CSV_PATH_ORDERS,
            TABLE_NAME_ORDERS,
            conn
        )

        build_database(
            CSV_PATH_SECRETS,
            TABLE_NAME_SECRETS,
            conn
        )
        conn.commit()

    finally:
        conn.close()


# ============================================================================
# Run only when this file is executed directly
# ============================================================================
if __name__ == "__main__":
    reset_database()