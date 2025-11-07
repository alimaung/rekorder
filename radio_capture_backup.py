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
import argparse
import signal
import sys
from datetime import datetime
import os

# Global flag to control recording
recording_active = True

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    global recording_active
    print(f"\nReceived signal {signum}. Stopping recording gracefully...")
    recording_active = False

# Function to capture the radio stream
def capture_radio_stream():
    global recording_active
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
    print("Press Ctrl+C to stop recording")
    
    try:
        with requests.get(stream_url, stream=True) as response:
            with open(output_file, 'wb') as out_file:
                # Write the stream data to the file
                for chunk in response.iter_content(chunk_size=8192):
                    if not recording_active:
                        print("Stopping recording...")
                        break
                    out_file.write(chunk)
                    out_file.flush()  # Ensure data is written immediately
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    except Exception as e:
        print(f"Error during recording: {e}")
    finally:
        if recording_active:
            print("Recording completed")
        else:
            print("Recording stopped")

# Main function to schedule the capture
def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Capture radio stream')
    parser.add_argument('--now', '-n', action='store_true', 
                       help='Record immediately instead of waiting for scheduled time')
    parser.add_argument('--duration', '-d', type=int, default=240,
                       help='Recording duration in minutes (default: 240 = 4 hours)')
    args = parser.parse_args()
    
    # If --now flag is used, record immediately
    if args.now:
        print(f"Recording immediately due to --now flag...")
        print(f"Will record for {args.duration} minutes")
        capture_radio_stream()
        return
    
    # Wait until 2100 CET on Friday
    print("Waiting for Friday at 21:00 CET...")
    while recording_active:
        try:
            now = datetime.now()
            if now.weekday() == 4 and now.hour == 21 and now.minute == 0:  # Friday at 2100
                print("Friday 21:00 reached! Starting recording...")
                capture_radio_stream()
                break
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nWaiting interrupted by user")
            break
    
    print("Script finished")

if __name__ == "__main__":
    main()

