# radio capture as background process saving radio streams on friday night
 
# radio station: planet radio:
# stream url: https://mp3.planetradio.de/planetradio/hqlivestream.aac

# Capture Nightwax session every Freitag at 2100 until 0100 CET

# Save to desktop folder: streams, filenames: planet_radio_nightwax_<date>.aac

# Externally:
# We schedule the task using Task Scheduler to start on boot and run every friday at 2045 
# So we need to wait until 2100 and capture the stream

import requests
import time
from datetime import datetime
import os

# Function to capture the radio stream
def capture_radio_stream():
    # Define the stream URL and output directory
    stream_url = "https://mp3.planetradio.de/planetradio/hqlivestream.aac"
    output_dir = os.path.expanduser("~/Desktop/streams")
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get the current date for the filename
    current_date = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(output_dir, f"planet_radio_nightwax_{current_date}.aac")

    # Start capturing the stream
    print(f"Capturing stream to {output_file}...")
    with requests.get(stream_url, stream=True) as response:
        with open(output_file, 'wb') as out_file:
            # Write the stream data to the file
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)

# Main function to schedule the capture
def main():
    # Wait until 2100 CET on Friday
    while True:
        now = datetime.now()
        if now.weekday() == 4 and now.hour == 21 and now.minute == 0:  # Friday at 2100
            capture_radio_stream()
            break
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()

