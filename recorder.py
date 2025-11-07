import requests
import keyboard  # Import the keyboard library
import threading  # Import threading to run capture in a separate thread

# planet , ufm
# 21 - 1 uhr planet radio
# ufm bigcitybeats 22-2 
# .aac datei
# audiacity
# desktop file, streamz, planet:nightwax, ufm:bcb

# 







url = "https://mp3.planetradio.de/planetradio/hqlivestream.aac"
#url = "https://bcb-stream28.radiohost.de/bcb-radio_mp3-192?ref=radiode"
is_capturing = False  # Flag to track if capturing is active

def start_capture():
    global is_capturing
    if not is_capturing:
        is_capturing = True
        print("Capture started.")
        response = requests.get(url, stream=True)
        with open("output2.aac", "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if not is_capturing:  # Check if capturing should stop
                    print("Capture stopped.")
                    break
                f.write(chunk)
        is_capturing = False  # Reset the flag when done
    else:
        print("Capture is already running.")

def stop_capture():
    global is_capturing
    if is_capturing:
        is_capturing = False
        print("Stopping capture...")
    else:
        print("Capture is not running.")

# Set up hotkeys
print("Press Ctrl+S to start capturing, Ctrl+E to stop capturing")

keyboard.add_hotkey('ctrl+s', lambda: threading.Thread(target=start_capture).start())  # Start capture in a new thread
keyboard.add_hotkey('ctrl+e', stop_capture)    # Stop capture with Ctrl + E

# Keep the program running
keyboard.wait('esc')  # Wait until the 'Esc' key is pressed to exit