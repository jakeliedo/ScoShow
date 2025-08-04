#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    import tkinter as tk
    print("✓ tkinter imported successfully")
    
    from tkinter import ttk, filedialog, messagebox
    print("✓ tkinter submodules imported successfully")
    
    import os
    import json
    print("✓ Standard modules imported successfully")
    
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    print("✓ PIL modules imported successfully")
    
    from screeninfo import get_monitors
    print("✓ screeninfo imported successfully")
    
    # Test creating a simple window
    root = tk.Tk()
    root.withdraw()  # Hide the window immediately
    
    print("✓ Tkinter window creation test successful")
    
    # Test monitors
    monitors = get_monitors()
    print(f"✓ Found {len(monitors)} monitor(s)")
    
    root.destroy()
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
