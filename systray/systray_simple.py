#!/usr/bin/env python3
"""
Simple System Tray Example with Recording Functionality
A basic test to ensure pystray works correctly with recording toggle
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Try to import pystray, install if not available
try:
    import pystray
    from pystray import MenuItem as item, Menu
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "pillow"])
    import pystray
    from pystray import MenuItem as item, Menu
    from PIL import Image, ImageDraw


class RecordingState:
    """Class to manage recording state"""
    def __init__(self):
        self.is_recording = False
    
    def toggle(self):
        """Toggle recording state"""
        self.is_recording = not self.is_recording
        return self.is_recording
    
    def get_status_text(self):
        """Get current status text"""
        return "Recording..." if self.is_recording else "Not Recording"
    
    def get_status_action_text(self):
        """Get text for status action item"""
        return "Stop Recording" if self.is_recording else "Start Recording"


# Global recording state
recording_state = RecordingState()


def create_default_icon():
    """Create a default icon"""
    width = 64
    height = 64
    color = 'blue'
    
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a simple icon
    dc.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill=color)
    dc.text((width//2-10, height//2-10), "ST", fill='white')
    
    return image


def load_icon(icon_name):
    """Load an icon from the systray directory"""
    script_dir = Path(__file__).parent
    icon_path = script_dir / icon_name
    
    if icon_path.exists():
        try:
            return Image.open(icon_path)
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            return None
    else:
        print(f"Icon file not found: {icon_path}")
        return None


def update_icon(icon):
    """Update the icon based on recording state"""
    if recording_state.is_recording:
        # Try to load red recording icon
        new_icon = load_icon("rec_red.ico")
        if new_icon:
            icon.icon = new_icon
            icon.tooltip = "Recording - Click to stop"
        else:
            # Fallback to default red icon
            icon.icon = create_red_icon()
            icon.tooltip = "Recording - Click to stop"
    else:
        # Try to load black icon
        new_icon = load_icon("rec_white.ico")
        if new_icon:
            icon.icon = new_icon
            icon.tooltip = "Not Recording - Click to start"
        else:
            # Fallback to default black icon
            icon.icon = create_black_icon()
            icon.tooltip = "Not Recording - Click to start"


def create_red_icon():
    """Create a red recording icon"""
    width = 64
    height = 64
    
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a red circle
    dc.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill='red')
    dc.text((width//2-10, height//2-10), "R", fill='white')
    
    return image


def create_black_icon():
    """Create a black icon"""
    width = 64
    height = 64
    
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a black circle
    dc.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill='black')
    dc.text((width//2-10, height//2-10), "S", fill='white')
    
    return image


def create_menu():
    """Create the menu with current recording state"""
    # Dynamic toggle text based on current state
    toggle_text = "Stop Recording" if recording_state.is_recording else "Start Recording"
    
    return Menu(
        item(toggle_text, toggle_recording),
        Menu.SEPARATOR,
        item("Show Message", show_message),
        item("Exit", quit_app)
    )


def update_menu(icon):
    """Update the menu with current recording state"""
    try:
        # Force menu update by recreating it
        icon.menu = create_menu()
    except Exception as e:
        print(f"Error updating menu: {e}")


def toggle_recording(icon, item):
    """Toggle recording state"""
    is_now_recording = recording_state.toggle()
    print(f"Recording {'started' if is_now_recording else 'stopped'}")
    update_icon(icon)
    # Force menu update
    update_menu(icon)


def show_message(icon, item):
    """Show a simple message"""
    print("Menu item clicked!")


def quit_app(icon, item):
    """Quit the application"""
    print("Exiting...")
    icon.stop()


def main():
    """Main function"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    icon_path = script_dir / "app-logo.ico"
    
    # Try to load the icon file, create a default one if not found
    if icon_path.exists():
        try:
            icon_image = Image.open(icon_path)
            print(f"Loaded icon: {icon_path}")
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_image = create_default_icon()
    else:
        print("Icon file not found, using default")
        icon_image = create_default_icon()
    
    # Create the system tray icon
    icon = pystray.Icon(
        "RecordingTest",
        icon_image,
        "Recording System Tray Test",
        create_menu()
    )
    
    print("Starting recording system tray application...")
    print("Right-click the system tray icon to see the menu")
    print("Click the icon to toggle recording state")
    
    # Set initial icon state
    update_icon(icon)
    
    try:
        # Run the icon
        icon.run()
    except Exception as e:
        print(f"Error running icon: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
