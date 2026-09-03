# ============================================================================
# Import required modules
# ============================================================================
import sqlite3            # Built-in Python module for SQLite databases (stores entire database inside a single file)
from pathlib import Path
import pandas as pd
import streamlit as st    # Streamlit is used to build interactive web applications with Python
from scripts.build_db import build_database, CSV_PATH, DB_PATH, TABLE_NAME
# Imports project-specific variables and functions:
# - build_database(): Creates a new SQLite database from the CSV file
# - CSV_PATH: Location of the original CSV file
# - DB_PATH: Location of the SQLite database file
# - TABLE_NAME: Name of the database table

# Configure the Streamlit page
st.set_page_config(
    page_title="SQL Playground",
    layout="wide"
)

# ============================================================================
# Helper functions
# ============================================================================
def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Note that the connection should always be closed after use.
    """
    return sqlite3.connect(DB_PATH)


def load_full_table() -> pd.DataFrame:
    """
    Loads database table into a Pandas DataFrame.
    """
    conn = get_connection()
    try:
        return pd.read_sql_query(
            f"SELECT * FROM {TABLE_NAME}",
            conn
        )
    finally:
        # Close the database connection, even if an error occurs.
        conn.close()


def run_query(query: str):
    """
    Executes an SQL statement entered by the user.
    Two different execution methods exist:
    - SELECT, PRAGMA and WITH statements return data, loaded as pd Dataframe (table unaltered)
    - INSERT, UPDATE, DELETE modify the database and must be
      committed so the changes are permanently saved.
    Returns:
        (DataFrame or None,
         status message or None,
         True if an error occurred, otherwise False)
    """
    conn = get_connection()
    try:
        # Remove spaces and convert to lowercase so that
        # the SQL command can be correctly interpreted
        stripped = query.strip().lower()
        # Type of queries that produce tabular results
        if (
            stripped.startswith("select")
            or stripped.startswith("pragma")
            or stripped.startswith("with")
        ):
            df = pd.read_sql_query(query, conn)
            return df, None, False

        # Queries that modify the database
        else:
            cursor = conn.cursor()
            # Execute the SQL statement
            cursor.execute(query)
            # Save the changes permanently
            conn.commit()
            return (
                None,
                f"Successfully executed. Rows affected: {cursor.rowcount}",
                False,
            )

    except Exception as e:
        # Return error message without stopping the application
        return None, str(e), True

    finally:
        # Close the database connection
        conn.close()


# ============================================================================
# Sidebar
# ============================================================================
# "st.sidebar" creates a permanent sidebar on the left side of the app.
# All Streamlit components inside this block are displayed there.
with st.sidebar:
    st.header("Settings")
    # Display information about the currently used data source
    st.write(f"CSV source: `{CSV_PATH.name}`")
    st.write(f"Table: `{TABLE_NAME}`")

    # Create a button: queries inside the if-block only run when the button is clicked
    if st.button(
        "🔄 Reset database from CSV",
        use_container_width=True
    ):
        # Rebuild the SQLite database using the original CSV file
        build_database()
        # Display a success message
        st.success("Database recreated from the CSV file.")
        # Reload the page so the update becomes visible
        st.rerun()

    st.markdown("---")

    # Display additional information in a smaller font
    st.caption(
        "Changes made with INSERT, UPDATE or DELETE affect the SQLite "
        "database. The button above recreates the original database from "
        "the CSV file at any time."
    )






# ============================================================================
# Ensure that the database exists
# ============================================================================
# Create the database automatically if it does not exist yet.
if not DB_PATH.exists():

    # A new database can only be created if the CSV file exists.
    if CSV_PATH.exists():
        build_database()

    else:
        # Display an error message inside the Streamlit app.
        st.error(
            f"Neither the database nor the CSV file was found.\n\n"
            f"Place the CSV file at `{CSV_PATH}` and reload the page."
        )

        # Stop execution so no further code is run.
        st.stop()


# ============================================================================
# Display the complete database table
# ============================================================================

# Main page title.
st.title("SQL Playground")

# Display the name of the current database table.
st.subheader(f"Sample table: {TABLE_NAME}")

# Load the entire table from the database.
full_df = load_full_table()

# Display the DataFrame as an interactive table.
st.dataframe(
    full_df,
    use_container_width=True,
    height=350
)

# Display the table dimensions.
st.caption(
    f"{len(full_df)} rows, {len(full_df.columns)} columns"
)

# Horizontal separator.
st.markdown("---")


# ============================================================================
# Split layout:
# Left side = SQL editor
# Right side = query result
# ============================================================================

# Create two equally sized columns.
left_col, right_col = st.columns(2)


# -----------------------------
# Left column: SQL editor
# -----------------------------
with left_col:

    st.subheader("SQL Query")

    # Default SQL statement shown when the page is first opened.
    default_query = f"SELECT * FROM {TABLE_NAME} LIMIT 10;"

    # Multi-line text input for entering SQL commands.
    query = st.text_area(
        "Enter an SQL query:",
        value=default_query,
        height=250,
        label_visibility="collapsed",
    )

    # Execute button.
    run_clicked = st.button(
        "▶ Run",
        type="primary"
    )


# -----------------------------
# Right column: Query results
# -----------------------------
with right_col:

    st.subheader("Result")

    # Only execute the SQL statement after the button has been clicked.
    if run_clicked:

        result_df, message, is_error = run_query(query)

        # Display an error message.
        if is_error:
            st.error(f"Error:\n\n{message}")

        # Display query results if a DataFrame was returned.
        elif result_df is not None:
            st.dataframe(
                result_df,
                use_container_width=True,
                height=350
            )

            st.caption(
                f"{len(result_df)} row(s) returned"
            )

        # Display the success message for INSERT, UPDATE, DELETE, etc.
        else:
            st.success(message)

    # Default message before any query has been executed.
    else:
        st.info(
            "Run an SQL query on the left to display the result here."
        )