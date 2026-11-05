import tkinter as tk
from tkinter import ttk
from ui.member_management import MemberManagementFrame
from ui.vendor_management import VendorManagementFrame
from ui.recommend_books import RecommendBooksFrame
from ui.recommended_report import RecommendedBooksFrame
from ui.theme import NAVY, TEAL, FONT_FAMILY


class DashboardFrame(ttk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, padding=0)
        self.user = user
        self.on_logout = on_logout
        self.pack(fill="both", expand=True)
        self.nav_buttons = {}

        self._build_topbar()
        self._build_sidebar_and_content()

    # ------------------------------------------------------------ layout --
    def _build_topbar(self):
        top = tk.Frame(self, bg=NAVY, height=64)
        top.pack(fill="x")
        top.pack_propagate(False)

        left = tk.Frame(top, bg=NAVY)
        left.pack(side="left", padx=20)
        tk.Label(left, text="📚", bg=NAVY, font=(FONT_FAMILY, 18)).pack(side="left", padx=(0, 8))
        tk.Label(
            left, text="Library Management System", bg=NAVY, fg="#FFFFFF",
            font=(FONT_FAMILY, 13, "bold"),
        ).pack(side="left")

        right = tk.Frame(top, bg=NAVY)
        right.pack(side="right", padx=20)
        ttk.Button(right, text="Logout", style="Logout.TButton", command=self.on_logout).pack(
            side="right", pady=14
        )
        user_wrap = tk.Frame(right, bg=NAVY)
        user_wrap.pack(side="right", padx=16)
        tk.Label(
            user_wrap, text=self.user["username"], bg=NAVY, fg="#FFFFFF",
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(anchor="e")
        tk.Label(
            user_wrap, text=self.user["role"], bg=NAVY, fg=TEAL,
            font=(FONT_FAMILY, 8),
        ).pack(anchor="e")

    def _build_sidebar_and_content(self):
        body = tk.Frame(self, bg="#F5F7FA")
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, width=240, bg=NAVY)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=NAVY, height=14).pack(fill="x")  # top breathing room

        content_wrap = tk.Frame(body, bg="#F5F7FA")
        content_wrap.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(content_wrap, bg="#F5F7FA")
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

        nav_items = [
            ("members", "👤  Manage Members", self.show_members),
            ("vendors", "🏬  Vendors & Exhibition", self.show_vendors),
            ("recommend", "🎯  Recommend Books", self.show_recommend),
            ("recommended", "⭐  Recommended Books", self.show_recommended),
        ]
        for key, text, cmd in nav_items:
            btn = ttk.Button(sidebar, text=text, style="Nav.TButton",
                              command=lambda k=key, c=cmd: self._select_nav(k, c))
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = btn

        self._select_nav("members", self.show_members)  # default view

    def _select_nav(self, key, cmd):
        for k, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if k == key else "Nav.TButton")
        cmd()

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # ----------------------------------------------------------- screens --
    def show_members(self):
        self._clear_content()
        MemberManagementFrame(self.content).pack(fill="both", expand=True)

    def show_vendors(self):
        self._clear_content()
        VendorManagementFrame(self.content).pack(fill="both", expand=True)

    def show_recommend(self):
        self._clear_content()
        RecommendBooksFrame(self.content).pack(fill="both", expand=True)

    def show_recommended(self):
        self._clear_content()
        RecommendedBooksFrame(self.content).pack(fill="both", expand=True)
