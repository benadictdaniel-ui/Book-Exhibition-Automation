import tkinter as tk
from tkinter import ttk, messagebox
import db
from ui.theme import NAVY, TEAL, CARD, TEXT_MUTED, FONT_FAMILY


class LoginFrame(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.pack(fill="both", expand=True)

        self._build_brand_panel()
        self._build_form_panel()

        self.bind_all("<Return>", lambda e: self.attempt_login())

    # ------------------------------------------------------------ panels --
    def _build_brand_panel(self):
        brand = tk.Frame(self, bg=NAVY, width=420)
        brand.pack(side="left", fill="both")
        brand.pack_propagate(False)

        wrap = tk.Frame(brand, bg=NAVY)
        wrap.place(relx=0.5, rely=0.46, anchor="center")

        tk.Label(wrap, text="📚", bg=NAVY, font=(FONT_FAMILY, 46)).pack(pady=(0, 10))
        tk.Label(
            wrap, text="Library Management\nSystem", bg=NAVY, fg="#FFFFFF",
            font=(FONT_FAMILY, 20, "bold"), justify="center",
        ).pack()
        tk.Label(
            wrap, text="Catalog · Members · Book Exhibition", bg=NAVY, fg=TEAL,
            font=(FONT_FAMILY, 11), justify="center",
        ).pack(pady=(8, 0))

        tk.Label(
            brand, text="v2.0  ·  Book Exhibition Automation", bg=NAVY, fg="#5B6C8F",
            font=(FONT_FAMILY, 9),
        ).pack(side="bottom", pady=16)

    def _build_form_panel(self):
        right = tk.Frame(self, bg="#F5F7FA")
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(right, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        card.place(relx=0.5, rely=0.46, anchor="center", width=340)

        pad = tk.Frame(card, bg=CARD)
        pad.pack(fill="both", expand=True, padx=36, pady=36)

        tk.Label(pad, text="Welcome back", bg=CARD, fg="#1E2430",
                 font=(FONT_FAMILY, 16, "bold")).pack(anchor="w")
        tk.Label(pad, text="Sign in to continue", bg=CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 10)).pack(anchor="w", pady=(2, 22))

        tk.Label(pad, text="USERNAME", bg=CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        self.username_var = tk.StringVar()
        ttk.Entry(pad, textvariable=self.username_var, font=(FONT_FAMILY, 11)).pack(
            fill="x", pady=(4, 16), ipady=4
        )

        tk.Label(pad, text="PASSWORD", bg=CARD, fg=TEXT_MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w")
        self.password_var = tk.StringVar()
        ttk.Entry(pad, textvariable=self.password_var, show="•", font=(FONT_FAMILY, 11)).pack(
            fill="x", pady=(4, 22), ipady=4
        )

        ttk.Button(
            pad, text="Login", style="Primary.TButton", command=self.attempt_login
        ).pack(fill="x", ipady=4)

        

    # ----------------------------------------------------------- actions --
    def attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing info", "Please enter both username and password.")
            return

        user = db.verify_login(username, password)
        if user:
            self.on_success(user)
        else:
            messagebox.showerror("Login failed", "Invalid username or password.")
