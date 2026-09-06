"""
Create a databse from csv file in Database/customer_data.csv
"""

# Import modules
import sqlite3
import sys
from pathlib import Path
import pandas as pd

# Declare relative paths and table name
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "SQL_APP" / "Database" / "customer_data.csv"
DB_PATH = PROJECT_ROOT / "SQL_APP" / "Database" / "sql_playground.db"
TABLE_NAME = "customer_data"

# Build the database from csv file
def build_database() -> None:
    # Catch error if data is not there
    if not CSV_PATH.exists():
        print(f"Error: CSV-File not found under: {CSV_PATH}")
        print("Please make sure that 'customer_data.csv' exists in the directory 'Database'.")
        sys.exit(1)

    # Read the file with pandas
    print(f"Reading CSV-file: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Found columns: {list(df.columns)}")
    print(f"Number of lines: {len(df)}")

    # Override DB if already existing
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Existing database has been replaced.")

    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql(TABLE_NAME, conn, index=False, if_exists="replace")
        conn.commit()
        print(f"Tabelle '{TABLE_NAME}' erfolgreich in {DB_PATH} erstellt.")
    finally:
        conn.close()


# Only run build_database() if this file is executed directly, not if it is imported by another file
if __name__ == "__main__":
    build_database()
