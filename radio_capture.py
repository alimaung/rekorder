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
import logging
import threading
from datetime import timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

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

# ------------------------------
# Logging setup and helpers
# ------------------------------
def setup_logger(logs_dir: str) -> logging.Logger:
    os.makedirs(logs_dir, exist_ok=True)
    logger = logging.getLogger("recorder")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    fh = logging.FileHandler(os.path.join(logs_dir, "recorder.log"), encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def get_berlin_tz(logger: logging.Logger):
    if ZoneInfo is not None:
        try:
            return ZoneInfo("Europe/Berlin")
        except Exception as exc:
            logger.warning(f"Could not load Europe/Berlin timezone: {exc}. Using local time.")
    else:
        logger.warning("zoneinfo not available. Install tzdata on Windows for accurate CET/CEST.")
    return None


def now_in_tz(tz) -> datetime:
    return datetime.now(tz) if tz else datetime.now()


def compute_next_window(logger: logging.Logger, tz, start_hour: int = 21, duration_hours: int = 4):
    current = now_in_tz(tz)
    days_ahead = (4 - current.weekday()) % 7  # Friday=4
    tentative = (current + timedelta(days=days_ahead)).replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if tentative <= current:
        tentative = tentative + timedelta(days=7)
    end_time = tentative + timedelta(hours=duration_hours)
    logger.info(f"Next window: {tentative} -> {end_time} ({'Europe/Berlin' if tz else 'local'})")
    return tentative, end_time


def wait_until(logger: logging.Logger, target_time: datetime, stop_event: threading.Event, check_interval_seconds: int = 10) -> bool:
    while not stop_event.is_set():
        now = target_time.tzinfo and datetime.now(target_time.tzinfo) or datetime.now()
        remaining = (target_time - now).total_seconds()
        if remaining <= 0:
            return True
        sleep_for = min(check_interval_seconds, max(1, int(remaining)))
        stop_event.wait(timeout=sleep_for)
    logger.info("Wait aborted by stop event")
    return False


# ------------------------------
# Robust recording with auto-reconnect and redundancy
# ------------------------------
def record_stream(logger: logging.Logger, stream_url: str, output_file_path: str, stop_event: threading.Event, end_time: datetime, thread_name: str) -> None:
    logger.info(f"[{thread_name}] Writing to {output_file_path}")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    backoff_seconds = 5
    max_backoff_seconds = 60
    session = requests.Session()
    try:
        with open(output_file_path, 'wb') as out_file:
            while not stop_event.is_set():
                now = end_time.tzinfo and datetime.now(end_time.tzinfo) or datetime.now()
                if now >= end_time:
                    logger.info(f"[{thread_name}] End time reached. Stopping.")
                    break
                try:
                    logger.info(f"[{thread_name}] Connecting to stream...")
                    with session.get(stream_url, stream=True, timeout=(10, 30)) as response:
                        response.raise_for_status()
                        logger.info(f"[{thread_name}] Connected. Recording...")
                        backoff_seconds = 5
                        for chunk in response.iter_content(chunk_size=64 * 1024):
                            if stop_event.is_set():
                                logger.info(f"[{thread_name}] Stop requested. Closing stream.")
                                return
                            now = end_time.tzinfo and datetime.now(end_time.tzinfo) or datetime.now()
                            if now >= end_time:
                                logger.info(f"[{thread_name}] End time reached mid-chunk. Closing stream.")
                                return
                            if chunk:
                                out_file.write(chunk)
                                out_file.flush()
                    logger.warning(f"[{thread_name}] Stream closed by server. Reconnecting...")
                except requests.RequestException as req_err:
                    logger.warning(f"[{thread_name}] Network error: {req_err}. Retrying in {backoff_seconds}s...")
                    stop_event.wait(timeout=backoff_seconds)
                    backoff_seconds = min(max_backoff_seconds, backoff_seconds * 2)
                except Exception as exc:
                    logger.error(f"[{thread_name}] Unexpected error: {exc}. Retrying in {backoff_seconds}s...")
                    stop_event.wait(timeout=backoff_seconds)
                    backoff_seconds = min(max_backoff_seconds, backoff_seconds * 2)
    finally:
        try:
            out_file.flush()
        except Exception:
            pass
        logger.info(f"[{thread_name}] Recorder thread finished.")


def start_redundant_recorders(logger: logging.Logger, stream_url: str, base_output_path: str, redundancy: int, stop_event: threading.Event, end_time: datetime):
    threads = []
    for idx in range(max(1, redundancy)):
        suffix = chr(97 + idx)  # a, b, c, ...
        output_file_path = f"{base_output_path}_{suffix}.aac" if redundancy > 1 else f"{base_output_path}.aac"
        thread_name = f"recorder-{suffix}"
        t = threading.Thread(
            target=record_stream,
            name=thread_name,
            args=(logger, stream_url, output_file_path, stop_event, end_time, thread_name),
            daemon=True,
        )
        t.start()
        threads.append(t)
    return threads

# Main function to schedule the capture
def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Planet Radio Nightwax recorder')
    parser.add_argument('--now', '-n', action='store_true', help='Record immediately instead of scheduled time')
    parser.add_argument('--duration', '-d', type=int, default=240, help='Duration in minutes for immediate mode (default 240)')
    parser.add_argument('--output-dir', '-o', default=os.path.expanduser('~/Desktop/streams'), help='Output directory for recordings')
    parser.add_argument('--redundancy', '-r', type=int, default=2, help='Number of parallel redundant streams (default 2)')
    parser.add_argument('--url', default='https://mp3.planetradio.de/planetradio/hqlivestream.aac', help='Stream URL override')
    args = parser.parse_args()

    logs_dir = os.path.join(args.output_dir, 'logs')
    logger = setup_logger(logs_dir)

    # Shared stop event for graceful shutdown
    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        logger.info(f"Received signal {signum}. Stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except Exception:
        pass

    tz = get_berlin_tz(logger)

    if args.now:
        started_at = now_in_tz(tz)
        end_time = started_at + timedelta(minutes=args.duration)
        date_str = started_at.strftime('%Y-%m-%d')
        base_filename = f"planet_radio_nightwax_{date_str}"
        base_output_path = os.path.join(args.output_dir, base_filename)
        logger.info(f"Immediate mode: recording until {end_time}")
        threads = start_redundant_recorders(logger, args.url, base_output_path, args.redundancy, stop_event, end_time)
        for t in threads:
            while t.is_alive():
                t.join(timeout=1)
                if stop_event.is_set():
                    break
        logger.info('Recording session finished.')
        return

    # Scheduled weekly mode
    logger.info('Scheduled mode: will record every Friday 21:00–01:00 Europe/Berlin')
    while not stop_event.is_set():
        start_time, end_time = compute_next_window(logger, tz, start_hour=21, duration_hours=4)
        reached = wait_until(logger, start_time, stop_event, check_interval_seconds=15)
        if not reached:
            break

        date_str = start_time.strftime('%Y-%m-%d')
        base_filename = f"planet_radio_nightwax_{date_str}"
        base_output_path = os.path.join(args.output_dir, base_filename)
        logger.info(f"Starting recording window {start_time} -> {end_time}")
        threads = start_redundant_recorders(logger, args.url, base_output_path, args.redundancy, stop_event, end_time)

        while not stop_event.is_set():
            now = now_in_tz(tz)
            if now >= end_time:
                logger.info('Window end reached. Waiting for threads to finish...')
                break
            stop_event.wait(timeout=5)

        for t in threads:
            while t.is_alive():
                t.join(timeout=1)
                if stop_event.is_set():
                    break

        logger.info('Recording window finished. Scheduling next week...')

    logger.info('Recorder stopped.')

if __name__ == "__main__":
    main()

