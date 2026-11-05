import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db
from excel_import import read_excel_rows
from ui.theme import style_tree_stripes, CARD, TEXT_MUTED, NAVY, FONT_FAMILY

# Acceptable header spellings per vendor sheet column, matched
# case/space-insensitively -- see excel_import.read_excel_rows.
BOOK_HEADER_MAP = {
    "title": ["Title", "Book Title"],
    "author": ["Author", "Author Name"],
    "subject": ["Subject"],
    "isbn": ["ISBN", "ISBN Number", "ISBN No"],
    "publisher": ["Publisher"],
    "category": ["Category", "Genre"],
}


class VendorManagementFrame(ttk.Frame):
    """
    Left: register vendors (add/update/delete) and pick one from the table.
    Right: the books that vendor is bringing to the fair, with an
    "Upload Excel" button that bulk-imports title/author/subject/isbn/
    publisher/category straight from the vendor's spreadsheet.
    """

    def __init__(self, master):
        super().__init__(master)
        self.selected_vendor_id = None
        self._build_header()

        body = tk.Frame(self, bg="#F5F7FA")
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#F5F7FA")
        left.pack(side="left", fill="y", padx=(0, 16))
        right = tk.Frame(body, bg="#F5F7FA")
        right.pack(side="left", fill="both", expand=True)

        self._build_vendor_form(left)
        self._build_vendor_table(left)
        self._build_books_panel(right)

        self.refresh_vendor_table()

    def _build_header(self):
        header = tk.Frame(self, bg="#F5F7FA")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="🏬 Vendors & Book Exhibition", bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 16, "bold")).pack(side="left")
        tk.Label(header, text="Register vendors and upload the books each one brings to the fair",
                  bg="#F5F7FA", fg=TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(10, 0), pady=(6, 0))

    # ------------------------------------------------------------ vendor --
    def _build_vendor_form(self, parent):
        card = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1, width=320)
        card.pack(fill="x", pady=(0, 12))
        form = ttk.Frame(card, style="Card.TFrame", padding=16)
        form.pack(fill="x")

        tk.Label(form, text="Vendor Details", bg=CARD, fg=NAVY,
                  font=(FONT_FAMILY, 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.vars = {
            "vendor_name": tk.StringVar(),
            "contact_person": tk.StringVar(),
            "phone": tk.StringVar(),
            "email": tk.StringVar(),
        }
        labels = [("Vendor Name", "vendor_name"), ("Contact Person", "contact_person"),
                  ("Phone", "phone"), ("Email", "email")]
        for i, (label, key) in enumerate(labels):
            tk.Label(form, text=label, bg=CARD, fg=TEXT_MUTED,
                      font=(FONT_FAMILY, 8, "bold")).grid(row=i * 2 + 1, column=0, sticky="w", padx=5)
            ttk.Entry(form, textvariable=self.vars[key], width=30).grid(
                row=i * 2 + 2, column=0, sticky="w", padx=5, pady=(2, 8)
            )

        btns = ttk.Frame(form, style="Card.TFrame")
        btns.grid(row=9, column=0, sticky="w", pady=(6, 0))
        ttk.Button(btns, text="➕ Add", style="Success.TButton", command=self.add_vendor).pack(side="left", padx=2)
        ttk.Button(btns, text="✎ Update", style="Primary.TButton", command=self.update_vendor).pack(side="left", padx=2)
        ttk.Button(btns, text="🗑 Delete", style="Danger.TButton", command=self.delete_vendor).pack(side="left", padx=2)
        ttk.Button(btns, text="Clear", style="Neutral.TButton", command=self.clear_form).pack(side="left", padx=2)

    def _build_vendor_table(self, parent):
        wrap = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        columns = ("id", "name", "contact", "phone")
        self.vendor_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        headers = {"id": "ID", "name": "Vendor", "contact": "Contact", "phone": "Phone"}
        widths = {"id": 35, "name": 130, "contact": 100, "phone": 90}
        for col in columns:
            self.vendor_tree.heading(col, text=headers[col])
            self.vendor_tree.column(col, width=widths[col], anchor="center" if col == "id" else "w")
        self.vendor_tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.vendor_tree.bind("<<TreeviewSelect>>", self.on_vendor_select)
        style_tree_stripes(self.vendor_tree)

    def refresh_vendor_table(self):
        for row in self.vendor_tree.get_children():
            self.vendor_tree.delete(row)
        for i, v in enumerate(db.search_vendors()):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.vendor_tree.insert("", "end", values=(
                v["vendor_id"], v["vendor_name"], v["contact_person"] or "-", v["phone"] or "-",
            ), tags=(tag,))

    def on_vendor_select(self, event):
        selected = self.vendor_tree.selection()
        if not selected:
            return
        values = self.vendor_tree.item(selected[0])["values"]
        self.selected_vendor_id = values[0]
        self.vars["vendor_name"].set(values[1])
        self.vars["contact_person"].set(values[2] if values[2] != "-" else "")
        self.vars["phone"].set(values[3] if values[3] != "-" else "")
        vendor = db.get_vendor(self.selected_vendor_id)
        self.vars["email"].set((vendor or {}).get("email") or "")
        self.books_title_var.set(f"Books from: {self.vars['vendor_name'].get()}")
        self.refresh_books_table()

    def _read_vendor_form(self):
        name = self.vars["vendor_name"].get().strip()
        if not name:
            messagebox.showwarning("Missing info", "Vendor Name is required.")
            return None
        return (name, self.vars["contact_person"].get().strip(),
                self.vars["phone"].get().strip(), self.vars["email"].get().strip())

    def add_vendor(self):
        data = self._read_vendor_form()
        if not data:
            return
        db.add_vendor(*data)
        messagebox.showinfo("Success", "Vendor added.")
        self.clear_form()
        self.refresh_vendor_table()

    def update_vendor(self):
        if self.selected_vendor_id is None:
            messagebox.showwarning("No selection", "Select a vendor first.")
            return
        data = self._read_vendor_form()
        if not data:
            return
        db.update_vendor(self.selected_vendor_id, *data)
        messagebox.showinfo("Success", "Vendor updated.")
        self.refresh_vendor_table()

    def delete_vendor(self):
        if self.selected_vendor_id is None:
            messagebox.showwarning("No selection", "Select a vendor first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this vendor and all their exhibition books?"):
            db.clear_vendor_books(self.selected_vendor_id)
            db.delete_vendor(self.selected_vendor_id)
            self.clear_form()
            self.refresh_vendor_table()

    def clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.selected_vendor_id = None
        self.vendor_tree.selection_remove(self.vendor_tree.selection())
        self.books_title_var.set("Select a vendor to see / upload their books")
        self.refresh_books_table()

    # ------------------------------------------------------------- books --
    def _build_books_panel(self, parent):
        bar = tk.Frame(parent, bg="#F5F7FA")
        bar.pack(fill="x", pady=(0, 8))
        self.books_title_var = tk.StringVar(value="Select a vendor to see / upload their books")
        tk.Label(bar, textvariable=self.books_title_var, bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 11, "bold")).pack(side="left")
        ttk.Button(bar, text="📤 Upload Excel", style="Primary.TButton",
                   command=self.upload_excel).pack(side="right")

        search_bar = tk.Frame(parent, bg="#F5F7FA")
        search_bar.pack(fill="x", pady=(0, 8))
        self.book_search_var = tk.StringVar()
        entry = ttk.Entry(search_bar, textvariable=self.book_search_var, width=34)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda e: self.refresh_books_table())
        tk.Label(search_bar, text="Search title / author / ISBN / category",
                  bg="#F5F7FA", fg=TEXT_MUTED, font=(FONT_FAMILY, 8)).pack(side="left", padx=8)

        wrap = tk.Frame(parent, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        columns = ("title", "author", "subject", "isbn", "publisher", "category")
        self.book_tree = ttk.Treeview(wrap, columns=columns, show="headings", height=14)
        headers = {"title": "Title", "author": "Author", "subject": "Subject",
                    "isbn": "ISBN", "publisher": "Publisher", "category": "Category"}
        widths = {"title": 190, "author": 130, "subject": 100, "isbn": 100, "publisher": 110, "category": 100}
        for col in columns:
            self.book_tree.heading(col, text=headers[col])
            self.book_tree.column(col, width=widths[col], anchor="w")
        self.book_tree.pack(fill="both", expand=True, padx=1, pady=1)
        style_tree_stripes(self.book_tree)

    def refresh_books_table(self):
        for row in self.book_tree.get_children():
            self.book_tree.delete(row)
        if self.selected_vendor_id is None:
            return
        for b in db.search_exhibition_books(self.book_search_var.get(), vendor_id=self.selected_vendor_id):
            self.book_tree.insert("", "end", values=(
                b["title"], b["author"], b["subject"] or "-", b["isbn"] or "-",
                b["publisher"] or "-", b["category"] or "-",
            ))

    def upload_excel(self):
        if self.selected_vendor_id is None:
            messagebox.showwarning("No vendor selected", "Select (or add) a vendor before uploading their book list.")
            return
        path = filedialog.askopenfilename(
            title="Select vendor book list (.xlsx)",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not path:
            return
        try:
            rows, missing = read_excel_rows(path, BOOK_HEADER_MAP)
        except Exception as e:
            messagebox.showerror("Could not read file", str(e))
            return
        if "title" in missing or "author" in missing:
            messagebox.showerror(
                "Missing columns",
                "The sheet must have at least Title and Author columns.\n"
                f"Columns not found: {', '.join(missing)}",
            )
            return
        inserted, skipped = db.bulk_add_exhibition_books(self.selected_vendor_id, rows)
        note = f"\n\nColumns not found in sheet: {', '.join(missing)}" if missing else ""
        messagebox.showinfo(
            "Import complete",
            f"Added {inserted} book(s).\nSkipped {skipped} row(s) missing Title/Author.{note}",
        )
        self.refresh_books_table()
