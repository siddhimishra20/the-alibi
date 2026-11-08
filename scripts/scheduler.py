#!/usr/bin/env python3
"""Background Cron Job & Daemon Scheduler for THE ALIBI.

Automates ahead-of-time pre-generation of non-repeating daily micro-crimes.
Supports:
1. Native Cron (0 0 * * 1 = Every Monday at 00:00)
2. macOS Launchd Agent (com.thealibi.pregenerator.plist)
3. Python Daemon background loop (rolling 14-day case buffer)
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = PROJECT_ROOT / ".venv" / "bin" / "python"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

CRON_COMMENT = "# THE ALIBI PRE-GENERATOR WEEKLY"
LAUNCHD_PLIST = Path.home() / "Library" / "LaunchAgents" / "com.thealibi.pregenerator.plist"

def run_pre_generation(days: int = 14) -> int:
    """Execute pre-generation of cases using the project's venv python."""
    cmd = [str(PYTHON_EXE), str(PROJECT_ROOT / "run.py"), "--pre-generate", str(days)]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running pre-generation ({days} days)...")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return res.returncode

def install_cron(days: int = 14) -> bool:
    """Install or update a weekly cron job (Every Monday at 00:00)."""
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    cron_log = logs_dir / "cron.log"

    cron_cmd = f"0 0 * * 1 cd {PROJECT_ROOT} && {PYTHON_EXE} run.py --pre-generate {days} >> {cron_log} 2>&1 {CRON_COMMENT}\n"

    try:
        # Get existing crontab
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current = res.stdout if res.returncode == 0 else ""
        
        # Remove any existing alibi cron line
        cleaned_lines = [line for line in current.splitlines() if CRON_COMMENT not in line]
        cleaned_lines.append(cron_cmd.strip())
        new_crontab = "\n".join(cleaned_lines) + "\n"

        proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
        if proc.returncode == 0:
            print(f"[✓] Cron job successfully installed! Scheduled for every Monday at 00:00.")
            print(f"    Command: {cron_cmd.strip()}")
            print(f"    Log file: {cron_log}")
            return True
        else:
            print(f"[✖] Failed to write crontab: {proc.stderr}")
            return False
    except Exception as e:
        print(f"[✖] Error installing cron job: {e}")
        return False

def uninstall_cron() -> bool:
    """Remove THE ALIBI cron job from the user's crontab."""
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if res.returncode != 0:
            print("No crontab found.")
            return True
        current = res.stdout
        cleaned_lines = [line for line in current.splitlines() if CRON_COMMENT not in line]
        new_crontab = "\n".join(cleaned_lines) + ("\n" if cleaned_lines else "")

        proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
        if proc.returncode == 0:
            print("[✓] THE ALIBI cron job removed.")
            return True
        else:
            print(f"[✖] Failed to update crontab: {proc.stderr}")
            return False
    except Exception as e:
        print(f"[✖] Error removing cron job: {e}")
        return False

def install_launchd(days: int = 14) -> bool:
    """Install a macOS launchd agent running every Monday at 00:00."""
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    cron_log = logs_dir / "cron.log"

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.thealibi.pregenerator</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_EXE}</string>
        <string>{PROJECT_ROOT}/run.py</string>
        <string>--pre-generate</string>
        <string>{days}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{PROJECT_ROOT}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{cron_log}</string>
    <key>StandardErrorPath</key>
    <string>{cron_log}</string>
</dict>
</plist>
"""
    try:
        LAUNCHD_PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(LAUNCHD_PLIST, "w", encoding="utf-8") as f:
            f.write(plist_content)
        subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST)], capture_output=True)
        res = subprocess.run(["launchctl", "load", str(LAUNCHD_PLIST)], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[✓] macOS Launchd Agent installed at {LAUNCHD_PLIST}")
            print(f"    Scheduled for every Monday at 00:00.")
            return True
        else:
            print(f"[!] Saved plist, but launchctl load reported: {res.stderr}")
            return True
    except Exception as e:
        print(f"[✖] Error installing launchd plist: {e}")
        return False

def uninstall_launchd() -> bool:
    """Unload and remove macOS launchd agent."""
    if LAUNCHD_PLIST.exists():
        subprocess.run(["launchctl", "unload", str(LAUNCHD_PLIST)], capture_output=True)
        LAUNCHD_PLIST.unlink(missing_ok=True)
        print("[✓] macOS Launchd Agent uninstalled.")
        return True
    print("No launchd plist found.")
    return True

def run_daemon_loop(check_interval_seconds: int = 3600, target_buffer_days: int = 14):
    """Continuous background loop keeping a rolling buffer of 14 future cases."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting THE ALIBI Daemon (Buffer: {target_buffer_days} days)...")
    while True:
        try:
            run_pre_generation(days=target_buffer_days)
        except Exception as e:
            print(f"[!] Daemon generation error: {e}")
        time.sleep(check_interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="THE ALIBI Background Case Pre-Generation Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run pre-generation immediately")
    parser.add_argument("--install-cron", action="store_true", help="Install weekly cron job (Every Monday 00:00)")
    parser.add_argument("--uninstall-cron", action="store_true", help="Uninstall weekly cron job")
    parser.add_argument("--install-launchd", action="store_true", help="Install macOS launchd agent (Every Monday 00:00)")
    parser.add_argument("--uninstall-launchd", action="store_true", help="Uninstall macOS launchd agent")
    parser.add_argument("--daemon", action="store_true", help="Run as a continuous background daemon process")
    parser.add_argument("--days", type=int, default=14, help="Number of days ahead to maintain (default: 14)")

    args = parser.parse_args()

    if args.install_cron:
        install_cron(days=args.days)
    elif args.uninstall_cron:
        uninstall_cron()
    elif args.install_launchd:
        install_launchd(days=args.days)
    elif args.uninstall_launchd:
        uninstall_launchd()
    elif args.daemon:
        run_daemon_loop(target_buffer_days=args.days)
    elif args.run_now:
        run_pre_generation(days=args.days)
    else:
        # Default interactive guide
        print("\n--- THE ALIBI SCHEDULER ---")
        print("Usage:")
        print("  python scripts/scheduler.py --install-cron      # Install weekly Monday 00:00 cron job")
        print("  python scripts/scheduler.py --install-launchd   # Install native macOS background agent")
        print("  python scripts/scheduler.py --daemon            # Run as a continuous background daemon")
        print("  python scripts/scheduler.py --run-now           # Generate 14 days right now\n")

if __name__ == "__main__":
    main()

