"""
This package is created solely as a method to avoid any sorts of conflicts and to ensure the right installation irrespective of the environment.
Created by: 
- Benjamin B C H
"""

packages = [
    "streamlit",
    "dotenv",
    "langchain_groq",
    "langchain_core"
]
import sys, subprocess

def install(packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)


if __name__ == "__main__":
    install(packages)
    
