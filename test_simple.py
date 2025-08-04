#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

def test_simple():
    root = tk.Tk()
    root.title("Test Simple")
    root.geometry("300x200")
    
    label = tk.Label(root, text="Test successful!", font=('Arial', 14))
    label.pack(expand=True)
    
    button = tk.Button(root, text="Close", command=root.destroy)
    button.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_simple()
