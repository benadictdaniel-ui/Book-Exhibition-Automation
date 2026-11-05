# Library Management System — Book Exhibition Automation

## How to run
1. Install Python 3.8+.
2. `python3 -m pip install openpyxl`   (the only extra package; use `python3 -m pip`, not bare `pip`)
3. In this folder: `python3 main.py`
4. Login: **admin / admin123**

Data lives in a local `library.db` (SQLite), created on first run.
> Upgrading from an older copy? Existing data is kept (the new *designation*
> column is added automatically). If you hit odd errors from very old test
> data, delete `library.db` once and start fresh.

## The workflow
1. **Manage Members** — choose **Student**, **Staff / Faculty** or **Researcher**.
   * Add people one by one (Member ID is typed by you: `STU101`, or the Emp ID for staff), or
   * click **Upload Faculty Excel** to load the whole staff list. Columns:
     `Emp ID · Name · Designation · Department · Email` (see `templates/faculty_template.xlsx`).
     Re-uploading a corrected sheet updates existing people instead of failing.
   * The **Show** buttons (All / Student / Staff / Researcher) list only the matching type.
2. **Vendors & Exhibition** — add a vendor, select it, **Upload Excel** with its books
   (`Title · Author · Subject · ISBN Number · Publisher · Category`, see `templates/vendor_books_template.xlsx`).
3. **Recommend Books** — pick the type, enter the Member/Emp ID (Name, Designation and Department
   auto-fill), search books from all vendors, set a quantity, add to the list and **Submit**.
4. **Recommended Books** — the final list.
   * A book offered by several vendors appears **once**: `Vendor A, Vendor B`, with the recommenders' names.
   * Books are treated as the same when title + author match (ignoring capitals/spacing).
   * Quantity: each recommender counts once per book (if they picked it from two vendors, the larger
     quantity is used); different recommenders' quantities add up.
   * **⬇ Admin Copy (Excel)** — one workbook: the merged list (with designation/department of each
     recommender) plus a *Recommendation Details* sheet.
   * **⬇ Vendor Copies (Excel)** — pick a folder; one workbook per vendor with only that vendor's
     titles and the quantity required (no recommender names).

## Project structure
```
main.py            entry point
db.py              schema + all queries (incl. the merged report)
excel_import.py    reads .xlsx uploads (header matching ignores case, spaces, punctuation)
export_excel.py    builds the admin and vendor Excel copies
templates/         sample Excel files for the two uploads
ui/                login, dashboard, member_management, vendor_management,
                   recommend_books, recommended_report, theme
```
