"""Style configurations for AutoRBI interface."""

import tkinter as tk
from tkinter import ttk


def configure_styles(root: tk.Tk) -> None:
    """Configure custom styles for the application."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # Custom button styles
    style.configure("Primary.TButton", padding=10, font=("Segoe UI", 10, "bold"))
    style.configure("Secondary.TButton", padding=8, font=("Segoe UI", 9))
    style.configure("Card.TLabelframe", padding=20, relief="flat", borderwidth=1)
    style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))

