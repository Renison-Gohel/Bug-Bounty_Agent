import os
import subprocess
import glob
import re
from typing import List, Optional
from langchain_core.tools import tool
# from playwright.sync_api import sync_playwright # Commented out to avoid dependency issues if not installed yet, can be enabled

@tool
def list_folders(path: str = ".") -> str:
    """List all directories in the given path."""
    try:
        items = os.listdir(path)
        folders = [item for item in items if os.path.isdir(os.path.join(path, item))]
        return "\n".join(folders) if folders else "No folders found."
    except Exception as e:
        return f"Error listing folders: {e}"

@tool
def list_files(path: str = ".") -> str:
    """List all files in the given path."""
    try:
        items = os.listdir(path)
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]
        return "\n".join(files) if files else "No files found."
    except Exception as e:
        return f"Error listing files: {e}"

@tool
def view_file(path: str) -> str:
    """Read and return the content of a file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def create_file(path: str, content: str) -> str:
    """Create or overwrite a file with the given content."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File created successfully at {path}"
    except Exception as e:
        return f"Error creating file: {e}"

@tool
def search_files(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern (e.g., '*.py', '**/*.txt')."""
    try:
        # recursive=True requires ** in pattern for recursive search
        matches = glob.glob(os.path.join(path, pattern), recursive=True)
        return "\n".join(matches) if matches else "No matches found."
    except Exception as e:
        return f"Error searching files: {e}"

@tool
def regex_search(pattern: str, path: str = ".") -> str:
    """Search for content matching a regex pattern in files within a directory (recursive)."""
    results = []
    try:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if re.search(pattern, content):
                            results.append(file_path)
                except:
                    continue
        return "\n".join(results) if results else "No matches found."
    except Exception as e:
        return f"Error performing regex search: {e}"

@tool
def run_security_audit(path: str) -> str:
    """Run basic static analysis tools (bandit for python) on the target path."""
    results = []
    
    # Check for Bandit (Python)
    try:
        # Only run if python files exist
        if any(f.endswith('.py') for r, d, f in os.walk(path) for f in f):
            cmd = ["bandit", "-r", path, "-f", "text"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            results.append(f"--- Bandit Results ---\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        results.append("Bandit not found. Install it with 'pip install bandit'.")
    except Exception as e:
        results.append(f"Error running bandit: {e}")

    # Add more tools here (e.g., semgrep) if available
    
    return "\n\n".join(results) if results else "No supported files found for audit or tools missing."

@tool
def terminal_command(command: str) -> str:
    """Execute a shell command and return its output (stdout + stderr).
    Use this to run system tools, network scanners, etc.
    """
    try:
        # Security precaution: In a real app, you'd want to sandbox this.
        # Here we assume the user is running this locally on their own machine/Kali.
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60 # 1 minute timeout to prevent hanging
        )
        output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error executing command: {e}"

# Placeholder for browser tool if needed, requires playwright install
# @tool
# def browser_tool(url: str) -> str:
#     ...
