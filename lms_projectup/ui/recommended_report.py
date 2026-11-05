import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import db
import export_excel
from ui.theme import style_tree_stripes, CARD, TEXT_MUTED, NAVY, FONT_FAMILY


class RecommendedBooksFrame(ttk.Frame):
    """
    The payoff screen: out of every book any vendor brought to the fair,
    only the ones someone recommended. A book offered by several vendors
    appears ONCE, with every vendor listed ("Vendor A, Vendor B") and every
    recommender named. From here the admin copy and the per-vendor copies
    are exported to Excel.
    """

    def __init__(self, master):
        super().__init__(master)
        self._build_header()
        self._build_toolbar()
        self._build_table()
        self.refresh_table()

    def _build_header(self):
        header = tk.Frame(self, bg="#F5F7FA")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="⭐ Recommended Books", bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 16, "bold")).pack(side="left")
        tk.Label(header, text="Each book once -- with every vendor and every recommender listed",
                  bg="#F5F7FA", fg=TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(10, 0), pady=(6, 0))

    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#F5F7FA")
        bar.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search_var, width=28)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda e: self.refresh_table())
        tk.Label(bar, text="Search title / author / ISBN / category / vendor / name", bg="#F5F7FA",
                  fg=TEXT_MUTED, font=(FONT_FAMILY, 8)).pack(side="left", padx=8)

        ttk.Button(bar, text="⟳", style="Neutral.TButton", width=3,
                   command=self.refresh_table).pack(side="right", padx=(6, 0))
        ttk.Button(bar, text="⬇ Vendor Copies (Excel)", style="Primary.TButton",
                   command=self.export_vendor_copies).pack(side="right", padx=(6, 0))
        ttk.Button(bar, text="⬇ Admin Copy (Excel)", style="Success.TButton",
                   command=self.export_admin_copy).pack(side="right")

    def _build_table(self):
        wrap = tk.Frame(self, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        columns = ("title", "author", "isbn", "vendors", "category", "qty", "recommenders")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", height=16)
        headers = {"title": "Title", "author": "Author", "isbn": "ISBN", "vendors": "Vendor(s)",
                    "category": "Category", "qty": "Total Qty", "recommenders": "Recommended By"}
        widths = {"title": 170, "author": 110, "isbn": 95, "vendors": 150,
                   "category": 80, "qty": 60, "recommenders": 170}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center" if col == "qty" else "w")
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)
        style_tree_stripes(self.tree)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, r in enumerate(db.get_recommended_books_report(self.search_var.get())):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                r["title"], r["author"], r["isbn"] or "-", r["vendors"],
                r["category"] or "-", r["total_quantity"], r["recommenders"],
            ), tags=(tag,))

    # ------------------------------------------------------------ exports --
    def _has_data(self):
        if not db.get_recommended_books_report():
            messagebox.showwarning("Nothing to export", "No books have been recommended yet.")
            return False
        return True

    def export_admin_copy(self):
        if not self._has_data():
            return
        path = filedialog.asksaveasfilename(
            title="Save admin copy",
            defaultextension=".xlsx",
            initialfile=f"Admin_Copy_{date.today().isoformat()}.xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not path:
            return
        try:
            count = export_excel.export_admin_copy(path)
        except Exception as e:
            messagebox.showerror("Export failed", str(e))
            return
        messagebox.showinfo("Admin copy saved", f"{count} book(s) exported to:\n{path}")

    def export_vendor_copies(self):
        if not self._has_data():
            return
        folder = filedialog.askdirectory(title="Choose a folder for the vendor copies")
        if not folder:
            return
        try:
            files = export_excel.export_vendor_copies(folder)
        except Exception as e:
            messagebox.showerror("Export failed", str(e))
            return
        names = "\n".join(f"  • {os.path.basename(p)}" for p in files)
        messagebox.showinfo("Vendor copies saved",
                            f"{len(files)} file(s) written to:\n{folder}\n\n{names}")
