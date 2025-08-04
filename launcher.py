#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple launcher for ScoShow Tournament Ranking Display
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher function"""
    try:
        print("Starting ScoShow Tournament Display...")
        
        # Import the main application
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        import json
        from PIL import Image, ImageTk, ImageDraw, ImageFont
        import threading
        import time
        from screeninfo import get_monitors
        
        print("All modules imported successfully")
        
        # Import tournament classes
        from scoshow import TournamentControlPanel
        
        # Create and run the application
        app = TournamentControlPanel()
        print("Tournament Control Panel created")
        
        app.run()
        
    except ImportError as e:
        print(f"Import error: {e}")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
