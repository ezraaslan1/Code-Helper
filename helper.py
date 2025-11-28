from datetime import timedelta
import time
import random
import ast
import sys
import os
from pynput import keyboard, mouse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

last_activity = None
last_afk_penalty = 0
last_line_count = 0
current_errors = 0
odds = 0.2
last_content = ""


def update_activity(_=None):
    global last_activity
    last_activity = time.time()

def afk_time():
    if last_activity is None:
        return 0
    return time.time() - last_activity

def clamp(value, min_val=0.0, max_val=1.0):
    return max(min_val, min(value, max_val))

def count_syntax_errors(filepath):
    try:
        with open(filepath, "r") as f:
            source = f.read()
        ast.parse(source)
        return 0
    except SyntaxError:
        return 1
    
def bet(balance):
    wager = input(f"You have ${balance}. Enter amount to wager: ")
    try:
        wager = float(wager)
        if wager > balance or wager < 0:
            print("Insufficient funds.")
            bet(balance)
    except ValueError:
        print("Enter a number.")
        bet(balance)
    return wager

def get_hours():
    hours = input("Hours: ")
    try:
        hours = float(hours)
        if hours < 0:
            print("Enter a valid number.")
            get_hours()
        elif hours > 5:
            go = input("That's a long time. Are you sure? (y/n): ")
            if go.lower() == "y":
                return hours
            else:
                get_hours()
    except ValueError:
        print("Enter a number.")
        get_hours()
    return hours

def get_minutes():
    minutes = input("Minutes: ")
    try:
        minutes = float(minutes)
        if minutes < 0:
            print("Enter a valid number.")
            get_minutes()
        elif minutes > 60:
            print("That's an hour. :)")
            get_minutes()
    except ValueError:
        print("Enter a number.")
        get_minutes()
    return minutes

class FileUpdateHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global current_errors, odds, last_line_count, last_content

        if os.path.abspath(event.src_path) != TARGET_FILE:
            return

        try:
            with open(TARGET_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_content = "".join(lines)
        except Exception:
            return

        old_lines = last_content.splitlines()
        new_lines = new_content.splitlines()

        afk_reset = False
        for i, new_line in enumerate(new_lines):
            old_line = old_lines[i] if i < len(old_lines) else ""
            if new_line != old_line and new_line.strip():
                afk_reset = True

        if afk_reset:
            update_activity()

        old_errors = current_errors
        current_errors = count_syntax_errors(TARGET_FILE)

        if current_errors < old_errors:
            odds += 0.01
        elif current_errors > old_errors:
            odds -= 0.01

        new_line_count = len(lines)

        if new_line_count > last_line_count:
            previous_normalized = set(l.strip() for l in old_lines if l.strip() != "")

            for i in range(last_line_count, new_line_count):
                raw_line = lines[i]
                stripped = raw_line.strip()
                if stripped == "":
                    continue
                #check for functions = more points
                if stripped.startswith("def "):
                    odds += 0.05

                #check for unique lines
                if stripped not in previous_normalized:
                    if current_errors == old_errors:
                        odds += 0.01
                    else:
                        odds -= 0.01

                    previous_normalized.add(stripped)

        last_line_count = new_line_count
        last_content = new_content

def main():
    global TARGET_FILE, last_line_count, last_afk_penalty, odds

    balance = 10

    user_input_path = input("Enter the path of the file you will be working on: ").strip()
    TARGET_FILE = os.path.abspath(user_input_path)

    if not os.path.exists(TARGET_FILE):
        print("Error: File does not exist.")
        return

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        last_line_count = len(f.readlines())

    TARGET_DIR = os.path.dirname(TARGET_FILE)

    try:
        with open(TARGET_FILE, "r") as f:
            last_line_count = len(f.readlines())
    except:
        last_line_count = 0

    #bet
    wager = bet(balance)

    balance -= wager

    print("How long will you code for?")
    hours = get_hours()
    minutes = get_minutes()
    goal_time = hours * 3600 + minutes * 60

    update_activity()
    last_afk_penalty = 0

    start_time = time.time()

    print("\nTimer started! Monitoring file...\n")

    observer = Observer()
    handler = FileUpdateHandler()
    observer.schedule(handler, TARGET_DIR, recursive=False)
    observer.start()

    print("Press Ctrl+C to stop.")

    try:
        while True:
            try:
                elapsed = time.time() - start_time
                remaining = max(0, goal_time - elapsed)

                afk_elapsed = afk_time()

                remaining_td = timedelta(seconds=remaining)
                remaining_str = str(remaining_td).split(".")[0]

                sys.stdout.write(
                    f"\rAFK: {afk_elapsed:6.1f}s   Odds: {100 * odds:.0f}%   Remaining: {remaining_str}s"
                )
                sys.stdout.flush()

                now = time.time()

                if now - last_afk_penalty >= 300:
                    if afk_elapsed >= 300:
                        odds -= 0.01
                        odds = clamp(odds)

                    last_afk_penalty = now

                if elapsed >= goal_time:
                    print("\nGoal complete!")
                    break

                time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nProgram ended before goal was reached.")
                return
    finally:
        observer.stop()
        observer.join()

    roll = random.random()
    if roll < odds:
        print("\nMoney doubled!")
        balance += wager * 2
    else:
        print("\nMoney lost.")

    print(f"Balance: ${balance}")

if __name__ == "__main__":
    main()
