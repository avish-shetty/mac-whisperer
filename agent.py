import subprocess
from google.adk import Agent

import os
import shutil
import fitz 
from pathlib import Path

def resolve_folder_path(folder_path: str):
    """
    Resolves a folder name or path.
    Returns:
        - A valid absolute path (str) if found
        - A dict with 'multiple_matches'
        - A dict with 'error'
    """

    folder_path = os.path.expanduser(folder_path)

    # If full valid path
    if os.path.isdir(folder_path):
        return folder_path

    home_dir = os.path.expanduser("~")
    matches = []

    for root, dirs, _ in os.walk(home_dir):
        for d in dirs:
            if d.lower() == folder_path.lower():
                matches.append(os.path.join(root, d))

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        return {"multiple_matches": matches[:5]}  # Limit to first 5 matches for brevity

    return {"error": f"No folder found matching '{folder_path}'"}

def get_largest_files(folder_path: str) -> str:
    """
    Finds largest files inside a folder.
    The folder_name can be a simple name like 'Documents' or a full path.
    """

    resolved = resolve_folder_path(folder_path)

    # If it's an error dict
    if isinstance(resolved, dict):
        if "multiple_matches" in resolved:
            paths = "\n".join(resolved["multiple_matches"])
            return {
                "status": "multiple_matches",
                "paths": resolved["multiple_matches"]
            }

        if "error" in resolved:
            return resolved["error"]

    # At this point it's a valid path
    result = subprocess.run(
        ['du', '-ah', resolved],
        capture_output=True,
        text=True
    )

    lines = result.stdout.splitlines()
    lines.sort(reverse=True)

    return "\n".join(lines[:10])


def read_pdf_preview(file_path: str) -> str:
    """Reads the first 500 characters of a PDF to identify its contents."""
    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
                if len(text) > 20000: break
            return text[:20000]
    except Exception as e:
        return f"Error reading PDF: {e}"

def move_file(source: str, destination_folder: str):
    """Moves a file to a specific folder. Creates the folder if it doesn't exist."""
    src_path = Path(source)
    dest_path = Path(destination_folder)
    dest_path.mkdir(parents=True, exist_ok=True)
    shutil.move(src_path, dest_path / src_path.name)
    return f"Successfully moved {src_path.name} to {destination_folder}"

def list_downloads():
    """Lists files in the Downloads folder."""
    downloads = Path.home() / "Downloads"
    return [str(f) for f in downloads.iterdir() if f.is_file() and not f.name.startswith('.')]

def check_disk_space():
    """Returns the current disk usage of the MacBook."""
    result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    return result.stdout

def check_memory_usage():
    """Returns current memory usage statistics."""
    result = subprocess.run(['vm_stat'], capture_output=True, text=True)
    return result.stdout

def check_battery_status():
    """Returns the current battery status."""
    result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
    return result.stdout

def list_network_interfaces():
    """Lists all network interfaces and their status."""
    result = subprocess.run(['ifconfig'], capture_output=True, text=True)
    return result.stdout

def check_uptime():
    """Returns how long the system has been running."""
    result = subprocess.run(['uptime'], capture_output=True, text=True)
    return result.stdout

def show_network_connections():
    """Shows active network connections."""
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    return result.stdout

def get_heavy_processes():
    """Returns the top 5 CPU-consuming processes."""
    result = subprocess.run(['ps', '-Ao', 'pcpu,comm', '-r'], capture_output=True, text=True)
    return "\n".join(result.stdout.splitlines()[:6])

# Define the Agent
root_agent = Agent(
    name="MacWhisperer",
    model="gemini-2.0-flash-lite", # Fast and cheap for local dev
    instruction="""You are a macOS expert. Help the user monitor their system. 
    Always explain technical stats in a friendly, witty way.
    Also, help the user manage their Downloads folder. If you find large files, suggest moving them to appropriate folders based on their content.
    1. Scan the Downloads folder using 'list_downloads'.
    2. Analyze the contents. If it's a PDF, use 'read_pdf_preview'.
    3. IMPORTANT: Do NOT move files immediately. Present a plan to the user first.
    4. Format your plan as: "I found [Filename]. I suggest moving it to [Folder] because [Reason]. Should I proceed?"
    5. Only use the 'move_file' tool AFTER the user says "Yes", "Proceed", or "Move them".
    6. If tool returns JSON with status=multiple_matches, display all paths exactly as provided.""",
    tools=[check_disk_space, get_heavy_processes, list_downloads, read_pdf_preview, move_file, check_memory_usage, check_battery_status, list_network_interfaces, check_uptime, show_network_connections,get_largest_files]
)