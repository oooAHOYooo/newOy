import subprocess
import sys
import time
import os
import webbrowser
import sqlite3
from importlib.metadata import version, PackageNotFoundError

def check_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists('data'):
        print("\n📁 Creating data directory...")
        os.makedirs('data')
        print("✅ Data directory created")

def check_db():
    """Check if database exists and is properly initialized"""
    db_path = 'data/ahoy.db'
    schema_path = 'schema.sql'
    
    if not os.path.exists(schema_path):
        print(f"❌ Error: schema.sql not found at {schema_path}")
        sys.exit(1)
        
    if not os.path.exists(db_path):
        print("\n🗃️ Initializing database...")
        try:
            conn = sqlite3.connect(db_path)
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.close()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            sys.exit(1)

def check_requirements():
    """Check if all requirements are installed"""
    try:
        with open('requirements.txt') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        missing = []
        for req in requirements:
            pkg_name = req.split('==')[0].lower()
            try:
                version(pkg_name)
            except PackageNotFoundError:
                missing.append(req)
        return missing
    except Exception as e:
        print(f"Error checking requirements: {e}")
        return []

def install_requirements():
    """Install missing requirements"""
    print("\n🔍 Checking requirements...")
    missing = check_requirements()
    
    if missing:
        print(f"\n📦 Installing {len(missing)} missing packages...")
        for package in missing:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("\n✅ All requirements installed successfully!")
    else:
        print("\n✅ All requirements are already installed!")

def show_loading():
    """Show a simple loading animation"""
    print("\n🚀 Starting the application...")
    for i in range(10):
        print(f"Loading... {i*10}%", end='\r')
        time.sleep(0.2)
    print("Loading... 100%")
    print("\n✨ Application is ready!")

def launch_browser():
    """Launch the default browser with the app URL"""
    print("\n🌐 Launching browser...")
    # Wait a moment for the Flask server to start
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:5001')

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║         Ahoy Application Starter      ║
    ╚══════════════════════════════════════╝
    """)
    
    try:
        # Check and create data directory
        check_data_dir()
        
        # Check and initialize database
        check_db()
        
        # Install requirements
        install_requirements()
        
        # Show loading animation
        show_loading()
        
        # Launch browser in a separate thread
        import threading
        browser_thread = threading.Thread(target=launch_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the Flask app
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 