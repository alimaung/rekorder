import curses
import requests
import threading
import os
import time
import tkinter as tk
from tkinter import filedialog

# Define radio stations
stations = {
    "Station 1": "https://bcb-stream28.radiohost.de/bcb-radio_mp3-192?ref=radiode",
    "Station 2": "https://mp3.planetradio.de/planetradio/hqlivestream.aac?aw_0_req.userConsentV2=CQOq1pgQOq1pgAfRuBDEBiFgAP_AAEPAAAigKGpVxCpcbWlGcTp3QPtkSYUX19gRIMQQAgCBISAFCAMA9JQG02EiMASABAACAQIAoxABAAAsGAhUAEAAQAAEAQDkAAAQgBEIIABEABAQQgJAAAgKAAgAEAAIgAA5EQAAmAiAIcKEDEAgQoAgKgAAAAABAAAFAAMAHEA4ABIAAAIAAYBAAgIAEACAAAEAAQgAAAAAAAAAAABAAAAAoAAAAAAABCChABIAoVEEJREAIRABhBAgBEFYQEQCAAAAAgSAAAAgAAOQEAFFhIgAAAAAAAAEAAIMAAQAACAAIRABAAEAAAAAAIAAAAAAQCAAAQAAQAEAAAAAICgAIAAAAAAAAAAAAAIAIACAAAAhAAEAAICoAAAAAAAAAAAAAABAAKAAAAAAAAAAAQAACABAAAAAAAAAAAAAAAAAAAAAAQAAAACAAAAAAAAQAA",
}

# Default export folder
default_export_folder = os.path.expanduser("~/Music")
export_folder = default_export_folder

# Global variables
is_capturing = False
recording_info = {"duration": 0, "filesize": 0, "filename": "output.aac"}
selected_station_index = 0
schedule_option = 0

def start_capture(station_url):
    global is_capturing, recording_info
    if not is_capturing:
        is_capturing = True
        recording_info["duration"] = 0
        recording_info["filesize"] = 0
        print("Capture started.")
        response = requests.get(station_url, stream=True)
        with open(os.path.join(export_folder, recording_info["filename"]), "wb") as f:
            start_time = time.time()
            for chunk in response.iter_content(chunk_size=1024):
                if not is_capturing:
                    print("Capture stopped.")
                    break
                f.write(chunk)
                recording_info["filesize"] += len(chunk)
                recording_info["duration"] = int(time.time() - start_time)
        is_capturing = False
    else:
        print("Capture is already running.")

def stop_capture():
    global is_capturing
    if is_capturing:
        is_capturing = False
        print("Stopping capture...")
    else:
        print("Capture is not running.")

def select_export_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_selected = filedialog.askdirectory(initialdir=default_export_folder)
    if folder_selected:
        global export_folder
        export_folder = folder_selected

def curses_final_dialog(stdscr, title, message):
    """Create a curses-based dialog for after recording."""
    h, w = 10, 60
    y, x = (curses.LINES - h) // 2, (curses.COLS - w) // 2
    dialog = curses.newwin(h, w, y, x)
    dialog.keypad(True)
    dialog.box()
    
    dialog.addstr(1, (w - len(title)) // 2, title, curses.A_BOLD)
    dialog.addstr(3, (w - len(message)) // 2, message)
    
    selected = 0  # 0 for OK
    options = ["OK"]
    
    while True:
        for i, option in enumerate(options):
            x_pos = w // 2 - 5 + i * 10
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            dialog.addstr(5, x_pos, option, attr)
        
        dialog.refresh()
        
        key = dialog.getch()
        
        if key == curses.KEY_ENTER or key in [10, 13]:
            break
    
def main(stdscr):
    global selected_station_index, recording_info, schedule_option
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    menu_options = [
        "Select Radio Station",
        "Select Export Folder",
        "Enter Filename",
        "Set Scheduler",
        "Start Recording",
        "Quit"
    ]
    
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Radio Recorder", curses.A_BOLD)
        
        for idx, option in enumerate(menu_options):
            if idx == selected_station_index:
                stdscr.addstr(idx + 2, 2, f"> {option} <", curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 2, option)
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP and selected_station_index > 0:
            selected_station_index -= 1
        elif key == curses.KEY_DOWN and selected_station_index < len(menu_options) - 1:
            selected_station_index += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
            if selected_station_index == 0:  # Select Radio Station
                stdscr.clear()
                stdscr.addstr(0, 0, "Select a station (use arrow keys):")
                for idx, station in enumerate(stations.keys()):
                    if idx == selected_station_index:
                        stdscr.addstr(2 + idx, 2, f"> {station} <", curses.A_REVERSE)
                    else:
                        stdscr.addstr(2 + idx, 2, station)
                stdscr.refresh()
                while True:
                    key = stdscr.getch()
                    if key == curses.KEY_UP and selected_station_index > 0:
                        selected_station_index -= 1
                    elif key == curses.KEY_DOWN and selected_station_index < len(stations) - 1:
                        selected_station_index += 1
                    elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
                        selected_station = list(stations.values())[selected_station_index]
                        break
                    elif key == 27:  # Esc key
                        break
                stdscr.clear()
            elif selected_station_index == 1:  # Select Export Folder
                select_export_folder()
            elif selected_station_index == 2:  # Enter Filename
                stdscr.clear()
                stdscr.addstr(0, 0, "Enter filename:")
                curses.echo()
                filename = stdscr.getstr(1, 0, 20).decode('utf-8')
                recording_info["filename"] = filename
                curses.noecho()
            elif selected_station_index == 3:  # Set Scheduler
                stdscr.clear()
                stdscr.addstr(0, 0, "Select Scheduler Option:")
                stdscr.addstr(1, 0, "1. From - To (Time and Date)")
                stdscr.addstr(2, 0, "2. From X with open ending until manually cancelled")
                stdscr.refresh()
                while True:
                    key = stdscr.getch()
                    if key == ord('1'):
                        schedule_option = 1
                        break
                    elif key == ord('2'):
                        schedule_option = 2
                        break
                    elif key == 27:  # Esc key
                        break
                stdscr.clear()
            elif selected_station_index == 4:  # Start Recording
                if 'selected_station' in locals():
                    threading.Thread(target=start_capture, args=(selected_station,)).start()
                    curses_final_dialog(stdscr, "Recording", "Recording started!")
            elif selected_station_index == 5:  # Quit
                break

        # Display recording info
        stdscr.addstr(10, 0, f"Duration: {recording_info['duration']} seconds")
        stdscr.addstr(11, 0, f"Filesize: {recording_info['filesize']} bytes")
        stdscr.refresh()

curses.wrapper(main) 