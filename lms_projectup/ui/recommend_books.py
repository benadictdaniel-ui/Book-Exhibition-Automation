import tkinter as tk
from tkinter import ttk, messagebox
import db
from ui.theme import style_tree_stripes, CARD, TEXT_MUTED, NAVY, FONT_FAMILY


class RecommendBooksFrame(ttk.Frame):
    """
    Purchase module: pick a recommender role (Student / Faculty /
    Researcher), enter their Member ID -- Name and Department auto-fill
    from the Manage Members table -- then browse the fair's books across
    all vendors and build a list to submit as recommendations with a
    quantity each.
    """

    def __init__(self, master):
        super().__init__(master)
        self.member = None
        self.cart = []  # dicts: exhibition_book_id, title, author, vendor_name, quantity
        self._build_header()

        body = tk.Frame(self, bg="#F5F7FA")
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#F5F7FA")
        left.pack(side="left", fill="y", padx=(0, 16))
        right = tk.Frame(body, bg="#F5F7FA")
        right.pack(side="left", fill="both", expand=True)

        self._build_recommender_panel(left)
        self._build_book_picker(right)
        self._build_cart_panel(right)

        self.refresh_book_table()

    def _build_header(self):
        header = tk.Frame(self, bg="#F5F7FA")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="🎯 Recommend Books (Purchase Module)", bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 16, "bold")).pack(side="left")
        tk.Label(header, text="Pick a recommender, choose books from the fair, and submit",
                  bg="#F5F7FA", fg=TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(10, 0), pady=(6, 0))

    # ------------------------------------------------------- recommender --
    def _build_recommender_panel(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1, width=300)
        card.pack(fill="x", pady=(0, 12))
        inner = ttk.Frame(card, style="Card.TFrame", padding=16)
        inner.pack(fill="x")

        tk.Label(inner, text="Who is recommending?", bg=CARD, fg=NAVY,
                  font=(FONT_FAMILY, 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.role_var = tk.StringVar(value="Student")
        for i, (r, label) in enumerate([("Student", "Student"), ("Faculty", "Staff / Faculty"),
                                        ("Researcher", "Researcher")]):
            ttk.Radiobutton(inner, text=label, value=r, variable=self.role_var,
                             command=self._on_role_change).grid(row=1, column=i, sticky="w", padx=2)

        tk.Label(inner, text="Member ID", bg=CARD, fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 8, "bold")).grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))
        self.member_id_var = tk.StringVar()
        id_entry = ttk.Entry(inner, textvariable=self.member_id_var, width=22)
        id_entry.grid(row=3, column=0, columnspan=3, sticky="w", pady=(2, 4))
        id_entry.bind("<Return>", lambda e: self.lookup_member())
        id_entry.bind("<FocusOut>", lambda e: self.lookup_member())
        tk.Label(inner, text="This is the ID shown in Manage Members", bg=CARD, fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 7)).grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.name_var = tk.StringVar(value="—")
        self.desig_var = tk.StringVar(value="—")
        self.dept_var = tk.StringVar(value="—")
        for i, (label, var) in enumerate([("Name", self.name_var),
                                          ("Designation", self.desig_var),
                                          ("Department", self.dept_var)]):
            tk.Label(inner, text=f"{label} (auto-filled)", bg=CARD, fg=TEXT_MUTED,
                      font=(FONT_FAMILY, 8, "bold")).grid(row=5 + i * 2, column=0, columnspan=3, sticky="w")
            tk.Label(inner, textvariable=var, bg=CARD, fg="#1E2430",
                      font=(FONT_FAMILY, 10, "bold")).grid(row=6 + i * 2, column=0, columnspan=3,
                                                          sticky="w", pady=(0, 6))

    def _on_role_change(self):
        self.member = None
        self.name_var.set("—")
        self.desig_var.set("—")
        self.dept_var.set("—")

    def lookup_member(self):
        raw_id = self.member_id_var.get().strip()
        if not raw_id:
            return
        member = db.get_member(raw_id)
        if not member:
            self.member = None
            self.name_var.set("Not found -- check Manage Members")
            self.desig_var.set("—")
            self.dept_var.set("—")
            return
        if member["role"] != self.role_var.get():
            messagebox.showwarning(
                "Role mismatch",
                f"Member #{raw_id} is registered as {member['role']}, not {self.role_var.get()}. "
                "Switching the selection to match.",
            )
            self.role_var.set(member["role"])
        self.member = member
        self.name_var.set(member["name"])
        self.desig_var.set(member.get("designation") or "—")
        self.dept_var.set(member.get("department") or "—")

    # -------------------------------------------------------- book picker --
    def _build_book_picker(self, parent):
        bar = tk.Frame(parent, bg="#F5F7FA")
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="🔎", bg="#F5F7FA", font=(FONT_FAMILY, 11)).pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search_var, width=34)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_book_table())
        tk.Label(bar, text="Search books from all vendors", bg="#F5F7FA",
                  fg=TEXT_MUTED, font=(FONT_FAMILY, 8)).pack(side="left")

        wrap = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        columns = ("id", "title", "author", "vendor", "category")
        self.book_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=8)
        headers = {"id": "ID", "title": "Title", "author": "Author", "vendor": "Vendor", "category": "Category"}
        widths = {"id": 0, "title": 220, "author": 140, "vendor": 130, "category": 100}
        for col in columns:
            self.book_tree.heading(col, text=headers[col])
            self.book_tree.column(col, width=widths[col], anchor="w", stretch=(col != "id"))
        self.book_tree["displaycolumns"] = ("title", "author", "vendor", "category")
        self.book_tree.pack(fill="both", expand=True, padx=1, pady=1)
        style_tree_stripes(self.book_tree)

        add_bar = tk.Frame(parent, bg="#F5F7FA")
        add_bar.pack(fill="x", pady=(6, 12))
        tk.Label(add_bar, text="Qty", bg="#F5F7FA", fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 9)).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(add_bar, textvariable=self.qty_var, width=6).pack(side="left", padx=(4, 12))
        ttk.Button(add_bar, text="➕ Add to Recommendation List", style="Primary.TButton",
                   command=self.add_to_cart).pack(side="left")

    def refresh_book_table(self):
        for row in self.book_tree.get_children():
            self.book_tree.delete(row)
        for b in db.search_exhibition_books(self.search_var.get()):
            self.book_tree.insert("", "end", values=(
                b["exhibition_book_id"], b["title"], b["author"], b["vendor_name"], b["category"] or "-",
            ))

    def add_to_cart(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showwarning("No book selected", "Select a book from the list first.")
            return
        qty_raw = self.qty_var.get().strip()
        if not qty_raw.isdigit() or int(qty_raw) < 1:
            messagebox.showwarning("Invalid quantity", "Quantity must be a positive number.")
            return
        book_id, title, author, vendor, category = self.book_tree.item(selected[0])["values"]
        for item in self.cart:
            if item["exhibition_book_id"] == book_id:
                item["quantity"] += int(qty_raw)
                self.refresh_cart_table()
                return
        self.cart.append({
            "exhibition_book_id": book_id, "title": title, "author": author,
            "vendor_name": vendor, "quantity": int(qty_raw),
        })
        self.refresh_cart_table()

    # -------------------------------------------------------------- cart --
    def _build_cart_panel(self, parent):
        tk.Label(parent, text="Selected for Recommendation", bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 11, "bold")).pack(anchor="w", pady=(0, 6))
        wrap = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        columns = ("title", "author", "vendor", "qty")
        self.cart_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=6)
        headers = {"title": "Title", "author": "Author", "vendor": "Vendor", "qty": "Qty"}
        widths = {"title": 220, "author": 140, "vendor": 130, "qty": 50}
        for col in columns:
            self.cart_tree.heading(col, text=headers[col])
            self.cart_tree.column(col, width=widths[col], anchor="center" if col == "qty" else "w")
        self.cart_tree.pack(fill="both", expand=True, padx=1, pady=1)
        style_tree_stripes(self.cart_tree)

        actions = tk.Frame(parent, bg="#F5F7FA")
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="🗑 Remove Selected", style="Danger.TButton",
                   command=self.remove_from_cart).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="✅ Submit Recommendation", style="Success.TButton",
                   command=self.submit_recommendation).pack(side="left")

    def refresh_cart_table(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for i, item in enumerate(self.cart):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.cart_tree.insert("", "end", values=(
                item["title"], item["author"], item["vendor_name"], item["quantity"],
            ), tags=(tag,))

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        index = self.cart_tree.index(selected[0])
        del self.cart[index]
        self.refresh_cart_table()

    def submit_recommendation(self):
        if self.member is None:
            messagebox.showwarning("No recommender", "Enter a valid Member ID first (add them in Manage Members if needed).")
            return
        if not self.cart:
            messagebox.showwarning("Empty list", "Add at least one book before submitting.")
            return
        for item in self.cart:
            db.add_recommendation(item["exhibition_book_id"], self.member["member_id"], item["quantity"])
        messagebox.showinfo(
            "Submitted",
            f"{len(self.cart)} book(s) recommended by {self.member['name']} ({self.member['role']}).",
        )
        self.cart = []
        self.refresh_cart_table()
