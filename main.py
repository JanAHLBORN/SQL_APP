# ============================================================================
# Import required modules
# ============================================================================
import sqlite3            # Built-in Python module for SQLite databases (stores entire database inside a single file)
from pathlib import Path
import pandas as pd
import streamlit as st    # Streamlit is used to build interactive web applications with Python
from build_db import build_database, CSV_PATH, DB_PATH, TABLE_NAME
# Imports project-specific variables and functions:
# - build_database(): Creates a new SQLite database from the CSV file
# - CSV_PATH: Location of the original CSV file
# - DB_PATH: Location of the SQLite database file
# - TABLE_NAME: Name of the database table

# Configure the Streamlit page
st.set_page_config(
    page_title="SQL Playground",
    layout="wide",
    page_icon=":dragon:",
    initial_sidebar_state="expanded",
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
# Exemplary tasks data
# ============================================================================
# A list of dictionaries, each representing one practice question.
# "question"    -> the task description shown to the user
# "answer"      -> the SQL statement that solves the task, revealed inside a
#                  collapsible dropdown (st.expander) so it is hidden by default
EXEMPLARY_TASKS = [
    {
        "question": "Show only the first name, surname, and country of every customer.",
        "answer": 'SELECT "First name", Surname, Country FROM customer_data;',
    },
    {
        "question": 'Find all purchases made by customers from "Germany".',
        "answer": "SELECT * FROM customer_data WHERE Country = 'Germany';",
    },
    {
        "question": "List all purchases ordered by Amount, highest first.",
        "answer": "SELECT * FROM customer_data ORDER BY Amount DESC;",
    },
    {
        "question": "Find the 5 highest-value purchases.",
        "answer": "SELECT * FROM customer_data ORDER BY Amount DESC LIMIT 5;",
    },
    {
        "question": "List all unique countries that appear in the table.",
        "answer": "SELECT DISTINCT Country FROM customer_data;",
    },
    {
        "question": "What is the total (sum) of all purchase amounts?",
        "answer": "SELECT SUM(Amount) AS total_revenue FROM customer_data;",
    },
    {
        "question": "Show the total amount spent per country.",
        "answer": (
            "SELECT Country, SUM(Amount) AS total_spent\n"
            "FROM customer_data\n"
            "GROUP BY Country;"
        ),
    },
    {
        "question": "Show only countries where total spending exceeds 1000.",
        "answer": (
            "SELECT Country, SUM(Amount) AS total_spent\n"
            "FROM customer_data\n"
            "GROUP BY Country\n"
            "HAVING SUM(Amount) > 1000;"
        ),
    },
    {
        "question": (
            "Find all names (first name + surname combination) that appear more than "
            "once in the table, e.g. because they bought multiple products."
        ),
        "answer": (
            'SELECT "First name", Surname, COUNT(*) AS num_purchases\n'
            "FROM customer_data\n"
            'GROUP BY "First name", Surname\n'
            "HAVING COUNT(*) > 1;"
        ),
    },
    {
        "question": 'Find all customers whose product name contains the word "Pro" (e.g. "Laptop Pro").',
        "answer": "SELECT * FROM customer_data WHERE Product LIKE '%Pro%';",
    },
    {
        "question": "Find all rows where Amount was not recorded (missing value).",
        "answer": "SELECT * FROM customer_data WHERE Amount IS NULL;",
    },
]


# ============================================================================
# Ensure that the database exists
# ============================================================================
# Create the database if it does not exist
if not DB_PATH.exists():
    # A new database is created (if the CSV file exists)
    if CSV_PATH.exists():
        build_database()
    else:
        # Display an error message inside the Streamlit app
        st.error(
            f"Neither the database nor the CSV file was found.\n\n"
            f"Place the CSV file at `{CSV_PATH}` and reload the page."
        )
        # Stop execution
        st.stop()


# ============================================================================
# Sidebar
# ============================================================================
# "st.sidebar" creates a permanent sidebar on the left side of the app.
# It scrolls independently from the main content whenever its content is
# taller than the visible window. A radio button at the top switches between
# the two sidebar views ("Settings" and "Exemplary Tasks") without needing a
# second sidebar, which Streamlit does not support natively.
with st.sidebar:
    sidebar_view = st.radio(
        "Sidebar navigation",
        ["Settings", "Exemplary Tasks"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("---")

    # -----------------------------
    # Sidebar view: Settings
    # -----------------------------
    if sidebar_view == "Settings":
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

    # -----------------------------
    # Sidebar view: Exemplary Tasks
    # -----------------------------
    else:
        st.header("Exemplary Tasks")
        st.caption(
            "Try writing the query yourself in the Playground first, then "
            "reveal the answer below."
        )

        # Loop through every task and render it as its own section.
        # "enumerate(..., start=1)" produces a running number starting at 1,
        # used to label each question (Question 1, Question 2, ...).
        for i, task in enumerate(EXEMPLARY_TASKS, start=1):
            st.markdown(f"**Question {i}:** {task['question']}")
            # A toggle hides the answer by default until switched on.
            if st.toggle("Show answer", key=f"answer_toggle_{i}"):
                # st.code renders the text as a formatted, read-only code
                # block with syntax highlighting for the given language.
                st.code(task["answer"], language="sql")
            st.markdown("---")


# ============================================================================
# Display the complete database table
# ============================================================================
# Main page title
st.title("SQL Playground")
# Display the name of the current database table
st.subheader(f"Sample table: {TABLE_NAME}")
# Load the entire table from the database
full_df = load_full_table()
# Display the DataFrame as an interactive table
st.dataframe(
    full_df,
    use_container_width=True,
    height=350
)
# Display the table dimensions
st.caption(
    f"{len(full_df)} rows, {len(full_df.columns)} columns"
)
# Horizontal separator
st.markdown("---")


# ============================================================================
# Split layout:
# Left side = SQL editor
# Right side = query result
# ============================================================================
# Create two equally sized columns
left_col, right_col = st.columns(2)
# -----------------------------
# Left column: SQL editor
# -----------------------------
with left_col:
    st.subheader("SQL Query")
    # Default SQL statement shown when the page is first opened
    default_query = f"SELECT * FROM {TABLE_NAME} LIMIT 10;"
    # Multi-line text input for entering SQL commands
    query = st.text_area(
        "Enter an SQL query:",
        value=default_query,
        height=250,
        label_visibility="collapsed",
    )
    # Execute button
    run_clicked = st.button(
        "▶ Run",
        type="primary"
    )

# -----------------------------
# Right column: Query results
# -----------------------------
with right_col:
    st.subheader("Result")
    # Only execute the SQL statement after the button has been clicked
    if run_clicked:
        result_df, message, is_error = run_query(query)
        # Display an error message
        if is_error:
            st.error(f"Error:\n\n{message}")
        # Display query results if a DataFrame was returned
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