"""Streamlit entry point: run with python -m streamlit run app.py."""
import sqlite3
from mindmate.config import load_settings
from mindmate.database import initialize_database
from mindmate.ui.landing import render_landing


def main():
    try:
        settings = load_settings()
        initialize_database(settings.database_path)
    except (OSError, sqlite3.Error, ValueError):
        import streamlit as st
        st.error("Unable to initialize local storage. Check the database path, permissions, and schema version. Existing files have not been replaced.")
        st.stop()
    try:
        render_landing(settings)
    except Exception:
        # Deliberately do not log unexpected exception objects: a dependency may
        # embed private text or headers in them. Control-flow reruns are BaseExceptions.
        import streamlit as st
        st.error("This page could not be completed. Refresh and check existing records before retrying a save. No automatic reset was performed.")


if __name__ == "__main__":
    main()
