"""
theme.py
--------
Pure presentation layer for the Library Management System.

This module contains ONLY visual definitions (colors, fonts, ttk styles).
It does not touch any business logic, database calls, or widget behavior --
importing it and calling apply_theme() just makes the existing widgets
(ttk.Frame, ttk.Button, ttk.Entry, ttk.Treeview, etc.) look nicer.
"""

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------- palette --
NAVY = "#1B2A4A"        # deep navy - topbar / sidebar / header
NAVY_DARK = "#131F38"   # sidebar hover
SLATE = "#3D5A80"       # secondary accent
TEAL = "#2E9E9E"        # primary accent / active nav
TEAL_DARK = "#237E7E"
GOLD = "#D9A441"        # highlights / warnings
CREAM = "#F5F7FA"       # app background
CARD = "#FFFFFF"        # card / panel background
BORDER = "#DDE3EC"
TEXT_DARK = "#1E2430"
TEXT_MUTED = "#6B7280"
SUCCESS = "#2E9E5B"
SUCCESS_DARK = "#237E48"
DANGER = "#D9534F"
DANGER_DARK = "#B94441"
INFO = "#3D5A80"
INFO_DARK = "#2F4763"
NEUTRAL = "#8A93A6"
NEUTRAL_DARK = "#6E7688"
ROW_ALT = "#EEF2F8"
ROW_SELECT = "#D7ECEC"

FONT_FAMILY = "Segoe UI"

FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11)
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_NAV = (FONT_FAMILY, 11)


def apply_theme(root):
    """Configure global ttk styles. Call once, right after creating the Tk root."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=CREAM)

    # ---- base ----------------------------------------------------------
    style.configure(".", font=FONT_BODY, background=CREAM, foreground=TEXT_DARK)
    style.configure("TFrame", background=CREAM)
    style.configure("TLabel", background=CREAM, foreground=TEXT_DARK, font=FONT_BODY)
    style.configure("TEntry", padding=6, relief="flat", fieldbackground="#FFFFFF")
    style.map("TEntry", bordercolor=[("focus", TEAL)])

    # ---- cards / label frames ------------------------------------------
    style.configure(
        "Card.TLabelframe", background=CARD, borderwidth=1, relief="solid"
    )
    style.configure(
        "Card.TLabelframe.Label", background=CARD, foreground=NAVY, font=FONT_HEADING
    )
    style.configure("Card.TFrame", background=CARD)
    # keep default LabelFrame usable too, just prettier
    style.configure("TLabelframe", background=CARD, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=CARD, foreground=NAVY, font=FONT_HEADING)

    # ---- buttons ---------------------------------------------------------
    style.configure(
        "TButton", font=FONT_BODY_BOLD, padding=(14, 8), relief="flat", borderwidth=0
    )

    def _button_style(name, base, hover, pressed, fg="#FFFFFF"):
        style.configure(name, background=base, foreground=fg)
        style.map(
            name,
            background=[("pressed", pressed), ("active", hover)],
            foreground=[("disabled", "#C9CED8")],
        )

    _button_style("Primary.TButton", TEAL, TEAL_DARK, TEAL_DARK)
    _button_style("Success.TButton", SUCCESS, SUCCESS_DARK, SUCCESS_DARK)
    _button_style("Danger.TButton", DANGER, DANGER_DARK, DANGER_DARK)
    _button_style("Info.TButton", INFO, INFO_DARK, INFO_DARK)
    _button_style("Neutral.TButton", NEUTRAL, NEUTRAL_DARK, NEUTRAL_DARK)
    _button_style("Logout.TButton", "#C1494A", "#A73B3C", "#A73B3C")

    # sidebar nav buttons (default / active look)
    style.configure(
        "Nav.TButton",
        font=FONT_NAV,
        padding=(14, 12),
        background=NAVY,
        foreground="#E9EDF5",
        borderwidth=0,
        anchor="w",
    )
    style.map(
        "Nav.TButton",
        background=[("active", NAVY_DARK)],
        foreground=[("active", "#FFFFFF")],
    )
    style.configure(
        "NavActive.TButton",
        font=FONT_NAV,
        padding=(14, 12),
        background=TEAL,
        foreground="#FFFFFF",
        borderwidth=0,
        anchor="w",
    )
    style.map("NavActive.TButton", background=[("active", TEAL_DARK)])

    # ---- treeview ----------------------------------------------------
    style.configure(
        "Treeview",
        background="#FFFFFF",
        fieldbackground="#FFFFFF",
        foreground=TEXT_DARK,
        rowheight=28,
        borderwidth=0,
        font=FONT_BODY,
    )
    style.configure(
        "Treeview.Heading",
        background=SLATE,
        foreground="#FFFFFF",
        font=FONT_BODY_BOLD,
        relief="flat",
        padding=(6, 8),
    )
    style.map("Treeview.Heading", background=[("active", NAVY)])
    style.map(
        "Treeview",
        background=[("selected", ROW_SELECT)],
        foreground=[("selected", TEXT_DARK)],
    )

    # ---- misc labels ----------------------------------------------------
    style.configure("Heading.TLabel", font=FONT_HEADING, foreground=NAVY, background=CREAM)
    style.configure("Muted.TLabel", font=FONT_SMALL, foreground=TEXT_MUTED, background=CREAM)
    style.configure("CardMuted.TLabel", font=FONT_SMALL, foreground=TEXT_MUTED, background=CARD)
    style.configure("CardLabel.TLabel", font=FONT_BODY_BOLD, foreground=TEXT_DARK, background=CARD)

    return style


def style_tree_stripes(tree):
    """Apply alternating row colors to a ttk.Treeview. Call after inserting rows."""
    tree.tag_configure("oddrow", background=ROW_ALT)
    tree.tag_configure("evenrow", background="#FFFFFF")


def stat_card(parent, icon, title, value, accent=TEAL):
    """Build a small dashboard-style stat card (icon + number + label) and return the frame."""
    card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    bar = tk.Frame(card, bg=accent, width=5)
    bar.pack(side="left", fill="y")
    inner = tk.Frame(card, bg=CARD)
    inner.pack(side="left", fill="both", expand=True, padx=14, pady=10)
    tk.Label(inner, text=icon, bg=CARD, font=(FONT_FAMILY, 18)).pack(anchor="w")
    tk.Label(inner, text=str(value), bg=CARD, fg=TEXT_DARK, font=(FONT_FAMILY, 18, "bold")).pack(anchor="w")
    tk.Label(inner, text=title, bg=CARD, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")
    return card
