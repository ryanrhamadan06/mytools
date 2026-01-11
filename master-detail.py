# master_detail.py
import os
import sys
import mysql.connector
from dotenv import load_dotenv
import importlib.util

def load_matching_master_detail_mod():
    """Load the master_detail_mod .pyd that matches the current Python version."""
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    
    # Build expected filename: e.g., master_detail_mod.cp312-win_amd64.pyd
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    pyd_filename = f"master_detail_mod.cp{py_major}{py_minor}-win_amd64.pyd"
    pyd_path = os.path.join(etc_dir, pyd_filename)

    if not os.path.isfile(pyd_path):
        raise FileNotFoundError(
            f"Required module not found: '{pyd_filename}' in 'etc/' folder.\n"
            f"This app needs a version compiled for Python {py_major}.{py_minor}."
        )

    spec = importlib.util.spec_from_file_location("master_detail_mod", pyd_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["master_detail_mod"] = module
    spec.loader.exec_module(module)
    return module

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        return None

def display_table_columns(connection, table_name):
    """
    Display all columns of a MySQL table with their metadata.
    
    Args:
        connection: Active mysql-connector connection object
        table_name (str): Name of the table to inspect
    """
    cursor = connection.cursor()
    try:
        query = """
        SELECT
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()

        if not columns:
            print(f"❌ Table '{table_name}' not found in current database.")
            return

        print(f"\n📌 Columns of table: `{table_name}`")
        print("-" * 80)
        print(f"{'Name':<20} {'Type':<25} {'NULL':<6} {'Default':<15} {'Extra'}")
        print("-" * 80)

        for col in columns:
            name, col_type, nullable, default_val, extra = col
            default_display = str(default_val) if default_val is not None else "NULL"
            nullable_display = "YES" if nullable == "YES" else "NO"
            print(f"{name:<20} {col_type:<25} {nullable_display:<6} {default_display:<15} {extra}")

        print("-" * 80)
        print(f"Total columns: {len(columns)}\n")

    except Exception as e:
        print(f"❌ Error fetching columns: {e}")
    finally:
        cursor.close()

def main():
    # Load .env from etc/ folder
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    dotenv_path = os.path.join(etc_dir, '.env')
    if not os.path.isfile(dotenv_path):
        raise FileNotFoundError("Missing .env file in 'etc/' folder")
    load_dotenv(dotenv_path)

    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    cursor.close()

    print("Available tables:")
    for i, t in enumerate(tables, 1):
        print(f"{i}. {t}")

    try:
        mid = int(input("\nPilih Tabel Master: ")) - 1
        did = int(input("Pilih Tabel Detail: ")) - 1
        if not (0 <= mid < len(tables)) or not (0 <= did < len(tables)):
            print("Invalid table selection.")
            return
    except ValueError:
        print("Please enter valid numbers.")
        return

    master_table = tables[mid]
    detail_table = tables[did]

    fkb_input = input(f"\nPilih Tabel Yang berelasi dengan Tabel {detail_table} (Enter untuk lewati): ").strip()
    if fkb_input == "":
        fk_detail_table = None
    else:
        try:
            fkb = int(fkb_input) - 1
            fk_detail_table = tables[fkb] if 0 <= fkb < len(tables) else None
        except ValueError:
            fk_detail_table = None

    module_name = input("Enter Module Name: ").strip()
    if not module_name:
        print("Module name cannot be empty.")
        return

    # Load the correct module for this Python version
    master_detail_mod = load_matching_master_detail_mod()

    master_cols = master_detail_mod.fetch_table_columns(connection, master_table)
    detail_cols = master_detail_mod.fetch_table_columns(connection, detail_table)

    display_table_columns(connection, master_table) 

    print("\nOptional enhancements:")
    unique_master = input(f"Field Unik di Tabel {master_table} (cth., nomor_bukti): ").strip() or None
    status_col = input(f"Field Status di Tabel {master_table} (cth., status_bayar): ").strip() or None
    total_col = input(f"Field total di tabel {master_table} (cth., total_items): ").strip() or None
    status_val = input("Berikan Status untuk mengakhiri transaksi (cth., LUNAS): ").strip() or None

    display_table_columns(connection, detail_table) 
    unique_col = input(f"Field unik di {detail_table} yang terkait dengan tabel lain (e.g., buku_id): ").strip() or None
    qty_col = input(f"Field di {detail_table} untuk menyimpan jumlah (e.g., qty): ").strip() or None
    price_col = input(f"Field di {detail_table} untuk menyimpan nilai uang (e.g., harga): ").strip() or None
    count_col = input(f"Field di {detail_table} untuk Update {total_col} in {master_table} (e.g., subtotal): ").strip() or None

    
    status_default = None
    if status_col:
        status_default = master_detail_mod.fetch_column_default(connection, master_table, status_col)

    # Generate master files
    files = {
        f"{module_name}/index.php": master_detail_mod.generate_master_index(module_name, master_table, master_cols, total_col),
        f"{module_name}/add.php": master_detail_mod.generate_master_add(
            module_name=module_name,
            master_table=master_table,
            master_cols=master_cols,
            detail_table=detail_table,
            connection=connection,
            total_col=total_col,
            status_col=status_col
        ),
        f"{module_name}/edit.php": master_detail_mod.generate_master_edit(module_name, master_table, master_cols),
        f"{module_name}/delete.php": master_detail_mod.generate_master_delete(module_name, master_table),
    }

    # Generate detail files
    detail_files = master_detail_mod.generate_detail_files(
        module_name=module_name,
        master_table=master_table,
        detail_table=detail_table,
        master_cols=master_cols,
        detail_cols=detail_cols,
        connection=connection,
        unique_detail_col=unique_col,
        master_total_col=total_col,
        detail_count_col=count_col,
        master_status_val=status_val,
        master_status_col=status_col,
        unique_master_col=unique_master,
        qty_col=qty_col,
        price_col=price_col,
        fk_detail_table=fk_detail_table
    )

    project_path = os.getenv('PROJECT_PATH')
    if not project_path:
        raise ValueError("PROJECT_PATH not found in .env file")

    # Let the module handle saving (as in your original design)
    master_detail_mod.save_generated_files(module_name, files, detail_files, project_path)

    connection.close()
    print("\n🎉 Master-Detail CRUD generated successfully!")

if __name__ == "__main__":
    main()