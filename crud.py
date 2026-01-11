# crud.py
import os
import sys
import mysql.connector
from dotenv import load_dotenv
import importlib.util

def load_matching_crud_mod():
    """Load the crud_mod .pyd that matches the current Python version."""
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    
    # Build expected filename: e.g., crud_mod.cp312-win_amd64.pyd
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    pyd_filename = f"crud_mod.cp{py_major}{py_minor}-win_amd64.pyd"
    pyd_path = os.path.join(etc_dir, pyd_filename)

    if not os.path.isfile(pyd_path):
        raise FileNotFoundError(
            f"Required module not found: '{pyd_filename}' in 'etc/' folder.\n"
            f"This app needs a version compiled for Python {py_major}.{py_minor}."
        )

    # Load the .pyd as a module
    spec = importlib.util.spec_from_file_location("crud_mod", pyd_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["crud_mod"] = module
    spec.loader.exec_module(module)
    return module

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return conn
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        return None

def fetch_table_info(connection, table_name):
    cursor = connection.cursor()
    cursor.execute(f"DESCRIBE `{table_name}`")
    cols = []
    for row in cursor.fetchall():
        name = row[0]
        typ = row[1].lower()
        nullable = (row[2] == 'YES')
        default = row[4] if row[4] is not None else None
        cols.append({'name': name, 'type': typ, 'nullable': nullable, 'default': default})
    cursor.close()
    return cols

def main():
    # Load .env from etc/ folder
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    dotenv_path = os.path.join(etc_dir, '.env')
    if not os.path.isfile(dotenv_path):
        raise FileNotFoundError("Missing .env file in 'etc/' folder")
    load_dotenv(dotenv_path)

    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    cursor.close()

    if not tables:
        print("No tables found.")
        return

    print("Available tables:")
    for i, t in enumerate(tables, 1):
        print(f"{i}. {t}")
    try:
        choice = int(input("Select table: ")) - 1
        if choice < 0 or choice >= len(tables):
            print("Invalid selection.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return
    table = tables[choice]

    cols = fetch_table_info(conn, table)

    # Load the correct crud_mod for this Python version
    crud_mod = load_matching_crud_mod()

    files = {
        f"{table}/index.php": crud_mod.generate_index_php(table, cols, conn),
        f"{table}/add.php": crud_mod.generate_add_php(table, cols, conn),
        f"{table}/edit.php": crud_mod.generate_edit_php(table, cols, conn),
        f"{table}/delete.php": crud_mod.generate_delete_php(table),
    }

    project_path = os.getenv('PROJECT_PATH')
    crud_mod.save_generated_files(files, project_path)
    conn.close()

if __name__ == "__main__":
    main()