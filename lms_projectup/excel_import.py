"""
excel_import.py
----------------
Small, dependency-light helper for reading vendor book lists and
student/faculty/researcher lists from .xlsx files with openpyxl.

Header matching is case- and space-insensitive, and each internal field
can accept several acceptable header spellings (e.g. "ISBN Number",
"ISBN No", "isbn"), so slightly different spreadsheet layouts from
different vendors still import correctly.

Install requirement (not in the Python standard library):
    pip install openpyxl
"""

from openpyxl import load_workbook


def _normalize(text):
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


def read_excel_rows(path, header_map):
    """
    Read the first sheet of an .xlsx file and return (rows, missing_fields).

    header_map: {internal_field_name: [acceptable header labels, ...]}
    The first row of the sheet is treated as the header row; every row
    after that is treated as data. Blank rows are skipped.

    rows: list of dicts, one per data row, keyed by internal_field_name.
          Any field whose column wasn't found is simply absent from
          rows and included in missing_fields instead of raising.
    missing_fields: list of internal_field_name that couldn't be matched
          to any column header, so the caller can warn the user.
    """
    wb = load_workbook(path, data_only=True, read_only=True)
    sheet = wb.active

    row_iter = sheet.iter_rows(values_only=True)
    try:
        header_row = next(row_iter)
    except StopIteration:
        return [], list(header_map.keys())

    normalized_headers = [_normalize(h) if h is not None else "" for h in header_row]

    col_index = {}
    missing_fields = []
    for field, aliases in header_map.items():
        found = None
        for alias in aliases:
            norm_alias = _normalize(alias)
            if norm_alias in normalized_headers:
                found = normalized_headers.index(norm_alias)
                break
        if found is None:
            missing_fields.append(field)
        else:
            col_index[field] = found

    rows = []
    for raw_row in row_iter:
        if raw_row is None or all(cell is None or str(cell).strip() == "" for cell in raw_row):
            continue  # skip blank rows
        record = {}
        for field, idx in col_index.items():
            value = raw_row[idx] if idx < len(raw_row) else None
            if isinstance(value, float) and value.is_integer():
                value = int(value)  # Excel often stores IDs like 1023 as 1023.0
            record[field] = str(value).strip() if value is not None else ""
        rows.append(record)

    wb.close()
    return rows, missing_fields
