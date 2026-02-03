import os
import shutil
import time
import threading
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ---------------------------------------------------------
# Load categories from config.json
# ---------------------------------------------------------
def load_config(): 
    try:
     # Detect correct path whether running as script or EXE
      base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
      config_path = os.path.join(base_path, "config.json")
      with open(config_path, "r") as f: return json.load(f)
    except Exception as e:
         messagebox.showerror("Error", f"Failed to load config.json:\n{e}")
         return {}


file_types = load_config()


# ---------------------------------------------------------
# Prevent duplicate filenames
# ---------------------------------------------------------
def get_unique_path(path):
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = f"{base} ({counter}){ext}"
        counter += 1
    return path


# ---------------------------------------------------------
# Organize a SINGLE file (real-time)
# ---------------------------------------------------------
def organize_single_file(file_path):
    folder_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)

    if os.path.isdir(file_path):
        return

    _, ext = os.path.splitext(file_name)
    ext = ext.lower()
    moved = False

    for category, extensions in file_types.items():
        if ext in extensions:
            category_folder = os.path.join(folder_path, category)
            os.makedirs(category_folder, exist_ok=True)

            destination = os.path.join(category_folder, file_name)
            destination = get_unique_path(destination)

            shutil.move(file_path, destination)
            print(f"[REALTIME] Moved {file_name} → {category}")
            moved = True
            break

    if not moved:
        other_folder = os.path.join(folder_path, "Others")
        os.makedirs(other_folder, exist_ok=True)

        destination = os.path.join(other_folder, file_name)
        destination = get_unique_path(destination)

        shutil.move(file_path, destination)
        print(f"[REALTIME] Moved {file_name} → Others")


# ---------------------------------------------------------
# Organize ALL existing files
# ---------------------------------------------------------
def organize_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        organize_single_file(file_path)


# ---------------------------------------------------------
# Watchdog real-time watcher
# ---------------------------------------------------------
class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            organize_single_file(event.src_path)


def start_watching(folder_path):
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    print("Watching for new files...")

    # Run watcher in background thread so GUI stays responsive
    def loop():
        try:
            while True:
                time.sleep(1)
        except:
            observer.stop()

    threading.Thread(target=loop, daemon=True).start()


# ---------------------------------------------------------
# GUI
# ---------------------------------------------------------
def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        organize_folder(folder)
        start_watching(folder)
        messagebox.showinfo("Done", "Real-time watching started!")


root = tk.Tk()
root.title("File Organizer Bot")
root.geometry("400x200")

# Set application icon
try:
    root.iconbitmap("favicon.ico")
except:
    print("Icon not found. Make sure icon.ico is in the same folder.")

btn = tk.Button(root, text="Choose Folder to Organize", command=choose_folder)
btn.pack(expand=True)

root.mainloop()
