import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db
from excel_import import read_excel_rows
from ui.theme import style_tree_stripes, CARD, TEXT_MUTED, NAVY, FONT_FAMILY

# Simple, standard email format check: something@something.something
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

ROLES = ("Student", "Faculty", "Researcher")
# "Faculty" is stored in the database; staff members are shown as "Staff / Faculty".
ROLE_LABELS = {"All": "All", "Student": "Student", "Faculty": "Staff / Faculty",
               "Researcher": "Researcher"}

# Accepted Excel header spellings for the faculty/staff list
# (matched ignoring case, spaces and punctuation -- see excel_import).
FACULTY_HEADER_MAP = {
    "member_id": ["Emp ID", "Employee ID", "Staff ID", "Faculty ID", "ID"],
    "name": ["Name", "Faculty Name", "Staff Name", "Employee Name"],
    "designation": ["Designation", "Post", "Position"],
    "department": ["Department", "Dept"],
    "email": ["Email", "Email ID", "Mail ID"],
}


class MemberManagementFrame(ttk.Frame):
    """
    Members are the single source of recommenders for the book-fair
    workflow. Each has a Role (Student / Staff-Faculty / Researcher), a
    staff-entered Member ID (the Emp ID for staff), Designation, Department
    and Email. Staff can be added one by one or uploaded in bulk from an
    Excel sheet of the faculty list.
    """

    def __init__(self, master):
        super().__init__(master)
        self.selected_member_id = None
        self._build_header()
        self._build_form()
        self._build_search_bar()
        self._build_table()
        self.refresh_table()

    def _build_header(self):
        header = tk.Frame(self, bg="#F5F7FA")
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="👤 Manage Members", bg="#F5F7FA", fg=NAVY,
                  font=(FONT_FAMILY, 16, "bold")).pack(side="left")
        tk.Label(header, text="Students, Staff / Faculty and Researchers -- also the recommender list for the book fair",
                  bg="#F5F7FA", fg=TEXT_MUTED, font=(FONT_FAMILY, 9)).pack(side="left", padx=(10, 0), pady=(6, 0))

    def _build_form(self):
        card = tk.Frame(self, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        card.pack(fill="x", pady=(0, 12))
        form = ttk.Frame(card, style="Card.TFrame", padding=16)
        form.pack(fill="x")

        tk.Label(form, text="Member Details", bg=CARD, fg=NAVY,
                  font=(FONT_FAMILY, 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # ---- role: Student / Staff / Researcher ----
        tk.Label(form, text="Type", bg=CARD, fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 8, "bold")).grid(row=1, column=0, sticky="w", padx=5)
        self.role_var = tk.StringVar(value="Student")
        role_bar = ttk.Frame(form, style="Card.TFrame")
        role_bar.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=(2, 10))
        for r in ROLES:
            ttk.Radiobutton(role_bar, text=ROLE_LABELS[r], value=r,
                             variable=self.role_var).pack(side="left", padx=(0, 14))

        # ---- Member ID (Emp ID for staff): staff-entered, locked after creation ----
        tk.Label(form, text="Member ID  (Emp ID for staff)", bg=CARD, fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 8, "bold")).grid(row=3, column=0, sticky="w", padx=5)
        self.id_var = tk.StringVar()
        self.id_entry = ttk.Entry(form, textvariable=self.id_var, width=24)
        self.id_entry.grid(row=4, column=0, sticky="w", padx=5, pady=(2, 0))
        tk.Label(form, text="e.g. STU101 for a student, or the employee ID for staff",
                  bg=CARD, fg=TEXT_MUTED, font=(FONT_FAMILY, 7)).grid(
            row=5, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 10))

        self.vars = {k: tk.StringVar() for k in
                     ("name", "designation", "department", "email", "phone", "address")}
        labels = [("Name", "name"), ("Designation", "designation"), ("Department", "department"),
                  ("Email", "email"), ("Phone", "phone"), ("Address", "address")]
        for i, (label, key) in enumerate(labels):
            r, c = divmod(i, 3)
            base_row = r * 2 + 6
            tk.Label(form, text=label, bg=CARD, fg=TEXT_MUTED,
                      font=(FONT_FAMILY, 8, "bold")).grid(row=base_row, column=c, sticky="w", padx=5)
            ttk.Entry(form, textvariable=self.vars[key], width=24).grid(
                row=base_row + 1, column=c, sticky="w", padx=5, pady=(2, 10)
            )

        btns = ttk.Frame(form, style="Card.TFrame")
        btns.grid(row=10, column=0, columnspan=3, sticky="w", pady=(6, 0))
        ttk.Button(btns, text="➕ Add Member", style="Success.TButton", command=self.add_member).pack(side="left", padx=4)
        ttk.Button(btns, text="✎ Update Selected", style="Primary.TButton", command=self.update_member).pack(side="left", padx=4)
        ttk.Button(btns, text="🗑 Delete Selected", style="Danger.TButton", command=self.delete_member).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear Form", style="Neutral.TButton", command=self.clear_form).pack(side="left", padx=4)
        ttk.Button(btns, text="📤 Upload Faculty Excel", style="Info.TButton",
                   command=self.upload_faculty_excel).pack(side="left", padx=(20, 4))
        tk.Label(form, text="Faculty Excel columns:  Emp ID · Name · Designation · Department · Email",
                  bg=CARD, fg=TEXT_MUTED, font=(FONT_FAMILY, 8)).grid(
            row=11, column=0, columnspan=3, sticky="w", padx=5, pady=(6, 0))

    def _build_search_bar(self):
        bar = tk.Frame(self, bg="#F5F7FA")
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="🔎", bg="#F5F7FA", font=(FONT_FAMILY, 11)).pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search_var, width=30)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        tk.Label(bar, text="Show:", bg="#F5F7FA", fg=TEXT_MUTED,
                  font=(FONT_FAMILY, 9, "bold")).pack(side="left", padx=(16, 4))
        self.filter_var = tk.StringVar(value="All")
        for r in ("All",) + ROLES:
            ttk.Radiobutton(bar, text=ROLE_LABELS[r], value=r, variable=self.filter_var,
                             command=self.refresh_table).pack(side="left", padx=4)

    def _build_table(self):
        wrap = tk.Frame(self, bg=CARD, highlightbackground="#DDE3EC", highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        columns = ("id", "name", "designation", "department", "email", "role", "phone")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", height=10)
        headers = {"id": "Member / Emp ID", "name": "Name", "designation": "Designation",
                    "department": "Department", "email": "Email", "role": "Type", "phone": "Phone"}
        widths = {"id": 105, "name": 130, "designation": 120, "department": 110,
                   "email": 160, "role": 95, "phone": 95}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center" if col in ("id", "role") else "w")
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        style_tree_stripes(self.tree)

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, m in enumerate(db.search_members(self.search_var.get(), role=self.filter_var.get())):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            # iid = the member ID, so selecting a row can reload the exact record
            # from the database (Treeview would turn IDs like "007" into 7).
            self.tree.insert("", "end", iid=str(m["member_id"]), values=(
                m["member_id"], m["name"], m["designation"] or "-", m["department"] or "-",
                m["email"] or "-", ROLE_LABELS.get(m["role"], m["role"]), m["phone"] or "-",
            ), tags=(tag,))

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        member = db.get_member(selected[0])
        if not member:
            return
        self.selected_member_id = member["member_id"]
        self.role_var.set(member["role"])
        self.id_var.set(member["member_id"])
        self.id_entry.configure(state="disabled")  # ID is locked once a member exists
        for key in self.vars:
            self.vars[key].set(member.get(key) or "")

    def _read_form(self, require_id=True):
        member_id = self.id_var.get().strip()
        name = self.vars["name"].get().strip()
        email = self.vars["email"].get().strip()
        phone = self.vars["phone"].get().strip()
        address = self.vars["address"].get().strip()
        department = self.vars["department"].get().strip()
        designation = self.vars["designation"].get().strip()
        role = self.role_var.get()

        if require_id and not member_id:
            messagebox.showwarning("Missing info", "Member ID is required.")
            return None
        if not name:
            messagebox.showwarning("Missing info", "Name is required.")
            return None
        if role != "Faculty" and not phone:
            messagebox.showwarning("Missing info", "Phone is required for students and researchers.")
            return None
        if email and not EMAIL_PATTERN.match(email):
            messagebox.showwarning(
                "Invalid email",
                "Please enter a valid email address (e.g. name@example.com).",
            )
            return None

        return member_id, name, email, phone, address, role, department, designation

    def add_member(self):
        data = self._read_form(require_id=True)
        if not data:
            return
        member_id, name, email, phone, address, role, department, designation = data
        try:
            db.add_member(member_id, name, email, phone, address, role, department, designation)
        except ValueError as e:
            messagebox.showerror("Could not add member", str(e))
            return
        messagebox.showinfo("Success", f"Member '{member_id}' added successfully.")
        self.clear_form()
        self.refresh_table()

    def update_member(self):
        if self.selected_member_id is None:
            messagebox.showwarning("No selection", "Select a member from the table first.")
            return
        data = self._read_form(require_id=False)
        if not data:
            return
        _, name, email, phone, address, role, department, designation = data
        try:
            db.update_member(self.selected_member_id, name, email, phone, address,
                             role, department, designation)
        except ValueError as e:
            messagebox.showerror("Could not update member", str(e))
            return
        messagebox.showinfo("Success", "Member updated successfully.")
        self.clear_form()
        self.refresh_table()

    def delete_member(self):
        if self.selected_member_id is None:
            messagebox.showwarning("No selection", "Select a member from the table first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete the selected member?"):
            try:
                db.delete_member(self.selected_member_id)
            except Exception:
                messagebox.showerror(
                    "Cannot delete",
                    "This member has recommendations recorded, so they cannot be deleted.",
                )
                return
            self.clear_form()
            self.refresh_table()

    def clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.role_var.set("Student")
        self.id_entry.configure(state="normal")
        self.id_var.set("")
        self.selected_member_id = None
        self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------- faculty Excel upload --
    def upload_faculty_excel(self):
        path = filedialog.askopenfilename(
            title="Select the faculty / staff list (.xlsx)",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if path:
            self.import_faculty_file(path)

    def import_faculty_file(self, path):
        """Read the sheet, add/update every faculty row, and show a summary."""
        try:
            rows, missing = read_excel_rows(path, FACULTY_HEADER_MAP)
        except Exception as e:
            messagebox.showerror("Could not read file", str(e))
            return None
        if "member_id" in missing or "name" in missing:
            messagebox.showerror(
                "Missing columns",
                "The sheet needs at least an Emp ID column and a Name column.\n"
                f"Columns not found: {', '.join(missing)}",
            )
            return None

        added, updated, skipped = db.bulk_add_members(rows, role="Faculty")

        msg = f"Added {added} new staff member(s).\nUpdated {updated} existing record(s)."
        if skipped:
            msg += f"\nSkipped {len(skipped)} row(s):"
            for row_no, reason in skipped[:6]:
                msg += f"\n  • Excel row {row_no}: {reason}"
            if len(skipped) > 6:
                msg += f"\n  • ...and {len(skipped) - 6} more"
        other_missing = [m for m in missing if m not in ("member_id", "name")]
        if other_missing:
            msg += f"\n\nColumns not found in sheet (left blank): {', '.join(other_missing)}"
        messagebox.showinfo("Import complete", msg)

        self.filter_var.set("Faculty")  # show the imported staff straight away
        self.refresh_table()
        return added, updated, skipped
