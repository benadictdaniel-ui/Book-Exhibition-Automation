"""
export_excel.py
----------------
Builds the two Excel copies produced at the end of a book fair:

  * Admin copy  -- one workbook with the merged recommended-books list
                   (a book offered by several vendors appears once, with all
                   its vendors listed) plus a details sheet showing exactly
                   who recommended what.
  * Vendor copy -- one workbook per vendor, listing only that vendor's books
                   and the quantity requested. Recommender names are left out.
"""

import os
import re
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import db

NAVY = "1B2A4A"
_HEADER_FILL = PatternFill(fill_type="solid", start_color=NAVY, end_color=NAVY)
_HEADER_FONT = Font(bold=True, color="FFFFFF")
_TOTAL_FILL = PatternFill(fill_type="solid", start_color="EEF2F8", end_color="EEF2F8")
_THIN = Side(style="thin", color="BBC3D0")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _write_table(ws, first_row, headers, rows, widths):
    """Write a styled header + data rows starting at first_row; returns the next free row."""
    for col, text in enumerate(headers, start=1):
        c = ws.cell(row=first_row, column=col, value=text)
        c.font = _HEADER_FONT
        c.fill = _HEADER_FILL
        c.border = _BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r_idx, row in enumerate(rows, start=first_row + 1):
        for col, value in enumerate(row, start=1):
            c = ws.cell(row=r_idx, column=col, value=value)
            c.border = _BORDER
            c.alignment = Alignment(vertical="top", wrap_text=True)
    for col, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.freeze_panes = ws.cell(row=first_row + 1, column=1)
    return first_row + 1 + len(rows)


def _title_block(ws, title, lines):
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14, color=NAVY)
    for i, text in enumerate(lines, start=2):
        ws.cell(row=i, column=1, value=text).font = Font(color="555555")


def _total_row(ws, row, label_col, label, total_col, total_value, last_col):
    for col in range(1, last_col + 1):
        c = ws.cell(row=row, column=col)
        c.fill = _TOTAL_FILL
        c.border = _BORDER
    ws.cell(row=row, column=label_col, value=label).font = Font(bold=True)
    ws.cell(row=row, column=total_col, value=total_value).font = Font(bold=True)


def export_admin_copy(path):
    """Write the admin workbook to `path`. Returns the number of distinct books exported."""
    books = db.get_recommended_books_report()
    details = db.get_recommendation_rows()
    today = date.today().isoformat()

    wb = Workbook()
    ws = wb.active
    ws.title = "Recommended Books"
    _title_block(ws, "Book Exhibition -- Recommended Books (Admin Copy)", [
        f"Generated on {today}",
        "A book offered by more than one vendor is listed once, with every vendor shown.",
    ])
    rows = [
        [i, b["title"], b["author"], b["isbn"], b["publisher"], b["category"],
         b["vendors"], b["total_quantity"], b["recommender_details"]]
        for i, b in enumerate(books, start=1)
    ]
    next_row = _write_table(
        ws, 5,
        ["S.No", "Title", "Author", "ISBN", "Publisher", "Category",
         "Vendor(s)", "Total Qty", "Recommended By"],
        rows, [7, 34, 24, 16, 20, 16, 28, 11, 46],
    )
    _total_row(ws, next_row, 7, "Total copies", 8,
               sum(b["total_quantity"] for b in books), 9)

    ws2 = wb.create_sheet("Recommendation Details")
    _title_block(ws2, "Recommendation Details -- every recommendation as submitted", [
        f"Generated on {today}",
    ])
    _write_table(
        ws2, 4,
        ["Book Title", "Author", "Vendor", "Member ID", "Name", "Role",
         "Designation", "Department", "Qty", "Date"],
        [[d["title"], d["author"], d["vendor_name"], d["member_id"], d["member_name"],
          d["role"], d["designation"] or "", d["department"] or "",
          d["quantity"], d["recommended_date"]] for d in details],
        [32, 22, 22, 12, 22, 12, 22, 20, 7, 12],
    )

    wb.save(path)
    return len(books)


def _safe_name(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "Vendor"


def export_vendor_copies(folder):
    """
    Write one workbook per vendor that has recommended books into `folder`.
    Returns the list of file paths written.
    """
    today = date.today().isoformat()
    written = []
    used_names = set()
    for entry in db.get_vendor_copy_data():
        vendor = entry["vendor"]
        items = entry["items"]

        filename = f"Vendor_{_safe_name(vendor['vendor_name'])}_{today}.xlsx"
        if filename in used_names:  # two vendors with the same name
            filename = f"Vendor_{_safe_name(vendor['vendor_name'])}_{vendor['vendor_id']}_{today}.xlsx"
        used_names.add(filename)
        path = os.path.join(folder, filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "Order List"
        contact = ", ".join(x for x in (vendor["contact_person"], vendor["phone"], vendor["email"]) if x)
        _title_block(ws, f"Library Book Exhibition -- Titles Requested from {vendor['vendor_name']}", [
            f"Generated on {today}",
            f"Vendor contact: {contact}" if contact else "",
        ])
        rows = [
            [i, it["title"], it["author"], it["isbn"], it["publisher"], it["category"], it["quantity"]]
            for i, it in enumerate(items, start=1)
        ]
        next_row = _write_table(
            ws, 5,
            ["S.No", "Title", "Author", "ISBN", "Publisher", "Category", "Quantity Required"],
            rows, [7, 36, 24, 16, 22, 16, 18],
        )
        _total_row(ws, next_row, 6, "Total copies", 7,
                   sum(it["quantity"] for it in items), 7)
        wb.save(path)
        written.append(path)
    return written
