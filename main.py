"""
app.py

SQL Playground - eine kleine Web-App zum Testen von SQL-Befehlen
gegen eine Beispieltabelle (customer_data), basierend auf SQLite.

Start:
    streamlit run app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.build_db import build_database, CSV_PATH, DB_PATH, TABLE_NAME

st.set_page_config(page_title="SQL Playground", layout="wide")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def load_full_table() -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    finally:
        conn.close()


def run_query(query: str):
    """
    Führt einen beliebigen SQL-Befehl aus.
    Gibt zurück: (dataframe_oder_None, meldung_oder_None, ist_fehler)
    """
    conn = get_connection()
    try:
        stripped = query.strip().lower()
        if stripped.startswith("select") or stripped.startswith("pragma") or stripped.startswith("with"):
            df = pd.read_sql_query(query, conn)
            return df, None, False
        else:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            return None, f"Erfolgreich ausgeführt. Betroffene Zeilen: {cursor.rowcount}", False
    except Exception as e:
        return None, str(e), True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Einstellungen")
    st.write(f"CSV-Quelle: `{CSV_PATH.name}`")
    st.write(f"Tabelle: `{TABLE_NAME}`")

    if st.button("🔄 Datenbank aus CSV zurücksetzen", use_container_width=True):
        build_database()
        st.success("Datenbank wurde neu aus der CSV-Datei aufgebaut.")
        st.rerun()

    st.markdown("---")
    st.caption(
        "Achtung: Änderungen per INSERT/UPDATE/DELETE wirken sich auf die "
        "SQLite-Datenbank aus. Mit dem Button oben kannst du jederzeit den "
        "Ursprungszustand aus der CSV-Datei wiederherstellen."
    )


# ---------------------------------------------------------------------------
# Prüfen, ob die DB existiert - falls nicht, initial erstellen
# ---------------------------------------------------------------------------

if not DB_PATH.exists():
    if CSV_PATH.exists():
        build_database()
    else:
        st.error(
            f"Weder Datenbank noch CSV-Datei gefunden.\n\n"
            f"Bitte lege deine Datei unter `{CSV_PATH}` ab und lade die Seite neu."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Obere Sektion: komplette Tabelle anzeigen
# ---------------------------------------------------------------------------

st.title("SQL Playground")
st.subheader(f"Beispieltabelle: {TABLE_NAME}")

full_df = load_full_table()
st.dataframe(full_df, use_container_width=True, height=350)
st.caption(f"{len(full_df)} Zeilen, {len(full_df.columns)} Spalten")

st.markdown("---")

# ---------------------------------------------------------------------------
# Untere Sektion: geteilter Bildschirm - SQL Eingabe / Ergebnis
# ---------------------------------------------------------------------------

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("SQL-Befehl")
    default_query = f"SELECT * FROM {TABLE_NAME} LIMIT 10;"
    query = st.text_area(
        "Gib hier deinen SQL-Befehl ein:",
        value=default_query,
        height=250,
        label_visibility="collapsed",
    )
    run_clicked = st.button("▶ Ausführen", type="primary")

with right_col:
    st.subheader("Ergebnis")
    if run_clicked:
        result_df, message, is_error = run_query(query)

        if is_error:
            st.error(f"Fehler:\n\n{message}")
        elif result_df is not None:
            st.dataframe(result_df, use_container_width=True, height=350)
            st.caption(f"{len(result_df)} Zeile(n) zurückgegeben")
        else:
            st.success(message)
    else:
        st.info("Führe links einen SQL-Befehl aus, um hier das Ergebnis zu sehen.")