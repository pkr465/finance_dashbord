"""
launch_streamlit.py

Please run from the project root; do NOT run from inside ui/.
The default Streamlit port is 8502; change here or in .env if needed.
"""

import os
import sys
import subprocess
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "localhost"
    finally:
        s.close()
    return ip

def print_dashboard_access_info():
    local_ip = "localhost"
    net_ip = get_local_ip()
    print("\nHow to access this dashboard:\n")
    print(f"On this machine: http://{local_ip}:8502")
    print(f"On another device on the same network: http://{net_ip}:8502")
    print('Note: "0.0.0.0" is a server listening address—not a real URL.')
    print("Always use 'localhost' or your computer's network IP as above.\n")

def main():
    # Check that we are being run from the project root and that ui/ exists
    if not os.path.isdir("ui"):
        print("ERROR: Please run this script from the project root directory (not from within ui/). Folder 'ui/' not found.")
        sys.exit(1)
    if not os.path.isfile("ui/streamlit_app.py"):
        print("ERROR: File 'ui/streamlit_app.py' not found in the ui/ directory.")
        sys.exit(1)
    print_dashboard_access_info()
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py", "--server.port", "8502"]
    )

if __name__ == "__main__":
    main()
