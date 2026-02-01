#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def main():
    dashboard_path = Path(__file__).parent / "dashboard" / "BasisMind.py"

    if not dashboard_path.exists():
        print(f"Error: {dashboard_path} not found")
        sys.exit(1)

    print("=" * 50)
    print("  BasisMind - Dashboard")
    print("=" * 50)
    print(f"\nStarting dashboard...")
    print("Open: http://localhost:8501\n")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ])


if __name__ == "__main__":
    main()
