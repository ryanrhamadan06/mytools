import os
import sys
import subprocess
from dotenv import load_dotenv
import importlib.util

def load_matching_installation_mod():
    """Load the installation_mod .pyd that matches the current Python version."""
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    
    # Build expected .pyd filename: e.g., installation_mod.cp312-win_amd64.pyd
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    pyd_filename = f"installation_mod.cp{py_major}{py_minor}-win_amd64.pyd"
    pyd_path = os.path.join(etc_dir, pyd_filename)

    if not os.path.isfile(pyd_path):
        raise FileNotFoundError(
            f"Required module not found: '{pyd_filename}' in 'etc/' folder.\n"
            f"This app needs a version compiled for Python {py_major}.{py_minor}."
        )

    # Load the .pyd as a module
    spec = importlib.util.spec_from_file_location("installation_mod", pyd_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["installation_mod"] = module  # Make it importable globally if needed
    spec.loader.exec_module(module)
    return module

def run_composer_install():
    """Run composer install using PROJECT_PATH from .env file"""
    # Load environment variables
    load_dotenv()
    
    # Get project path
    project_path = os.getenv('PROJECT_PATH')
    
    if not project_path:
        print("Error: PROJECT_PATH not set in .env file")
        return False
    
    print(f"Running composer install in: {project_path}")
    
    # Change to the project directory
    original_dir = os.getcwd()
    os.chdir(project_path)
    
    try:
        # Run composer install using os.system
        result = os.system("composer install")
        
        if result == 0:
            print("✓ composer install completed successfully!")
        else:
            print(f"✗ composer install failed (code: {result})")
        
        return result == 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Return to original directory
        os.chdir(original_dir)

def main():
    # Load .env from etc/ folder
    etc_dir = os.path.join(os.path.dirname(__file__), 'etc')
    dotenv_path = os.path.join(etc_dir, '.env')
    if not os.path.isfile(dotenv_path):
        raise FileNotFoundError("Missing .env file in 'etc/' folder")
    load_dotenv(dotenv_path)

    project_path = os.getenv('PROJECT_PATH')
    if not project_path:
        raise ValueError("Missing PROJECT_PATH in .env")

    # Load the correct .pyd module for this Python version
    installation_mod = load_matching_installation_mod()

    print("Creating project structure...")
    installation_mod.create_structure(installation_mod.project_structure)
    
    print("\nInitializing database...")
    installation_mod.create_database_and_table()
    
    input("Press Enter to install composer library...")
    run_composer_install()
    
    print("\nInstalasi Project telah selesai!.")

if __name__ == "__main__":
    main()