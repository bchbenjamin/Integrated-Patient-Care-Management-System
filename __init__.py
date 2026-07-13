"""
This package is created solely as a method to avoid any sorts of conflicts and to ensure the right installation irrespective of the environment.
Created by: 
- Benjamin B C H
"""

import sys
import subprocess
import importlib

# Map python module import name -> pip package installation name
packages_map = {
    "streamlit": "streamlit",
    "dotenv": "python-dotenv",
    "langchain_groq": "langchain-groq",
    "langchain_core": "langchain-core",
    "pymysql": "pymysql",
    "bcrypt": "bcrypt",
    "plotly": "plotly",
    "streamlit_calendar": "streamlit-calendar",
    "pandas": "pandas"
}

def install_missing():
    missing = []
    for module_name, package_name in packages_map.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        print(f"Installing missing packages: {missing}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        except Exception as e:
            print(f"Error installing packages: {e}")

# Run automatic check and install when package is imported or run directly
install_missing()

if __name__ == "__main__":
    print("All packages verified and installed successfully.")
