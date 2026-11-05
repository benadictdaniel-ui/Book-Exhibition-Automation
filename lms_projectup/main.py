"""
Library Management System — Book Exhibition Automation
--------------------------------------------------------
Entry point. Run with:  python main.py

Default admin login:
    username: admin
    password: admin123
"""

import tkinter as tk
from tkinter import ttk
import db
from ui.login import LoginFrame
from ui.dashboard import DashboardFrame
from ui.theme import apply_theme, CREAM


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1300x740")
        self.minsize(1050, 620)
        self.configure(bg=CREAM)

        apply_theme(self)

        self.current_frame = None
        self.show_login()

    def _clear(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_login(self):
        self._clear()
        self.current_frame = LoginFrame(self, on_success=self.show_dashboard)

    def show_dashboard(self, user):
        self._clear()
        self.current_frame = DashboardFrame(self, user, on_logout=self.show_login)


if __name__ == "__main__":
    db.init_db()
    app = LibraryApp()
    app.mainloop()
