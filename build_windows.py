import PyInstaller.__main__
import os
import shutil
import platform
import webbrowser
from flask import Flask

def create_launcher_script():
    """Create a launcher script that will start the Flask app and open the browser"""
    launcher_code = '''
import os
import sys
import threading
import time
import webbrowser
from flask import Flask

def open_browser():
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://127.0.0.1:5000')

def main():
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Import and run the Flask app
    from app import app
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main()
'''
    with open('launcher.py', 'w') as f:
        f.write(launcher_code)

def build_app():
    # Create launcher script
    create_launcher_script()
    
    # Ensure the dist directory is clean
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

    # Determine the separator for the current OS
    separator = ';' if platform.system() == 'Windows' else ':'
    
    # Define the PyInstaller arguments
    args = [
        'launcher.py',  # Use our launcher script as the entry point
        f'--name=AhoyIndieMedia',  # Name of your executable
        '--onefile',  # Create a single executable
        '--windowed',  # Don't show console window
        f'--add-data=templates{separator}templates',  # Include templates directory
        f'--add-data=static{separator}static',  # Include static directory
        f'--add-data=instance{separator}instance',  # Include instance directory
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--clean',  # Clean PyInstaller cache
    ]

    # Add icon if it exists
    if os.path.exists('static/favicon.ico'):
        args.append('--icon=static/favicon.ico')

    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    # Clean up launcher script
    if os.path.exists('launcher.py'):
        os.remove('launcher.py')

if __name__ == '__main__':
    build_app() 