"""
Air Canvas - Hand Gesture Based Virtual Drawing System
======================================================
Main entry point. Run this file to start the application.

Usage:
    python main.py

Controls:
    - Index finger up       → Draw
    - Two fingers up        → Move (no drawing)
    - All fingers open      → Clear canvas
    - Hover top menu        → Select color / tool
    - Press 'S'             → Save drawing
    - Press 'Q' or ESC      → Quit
"""

from air_canvas import AirCanvas


def main():
    app = AirCanvas()
    app.run()


if __name__ == "__main__":
    main()
