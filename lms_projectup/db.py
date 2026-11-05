"""
db.py
-------
Database access layer for the Library Management System (Book Exhibition
Automation build).

BOOK EXHIBITION AUTOMATION (v4):
- member: Students / Faculty / Researchers. Each one has a Role and an
  optional Department. Member IDs are now entered by staff, not
  auto-numbered -- students and staff typically use different ID formats
  (e.g. STU101 vs FAC204), so the ID field is free text.
- vendor / exhibition_book: vendors attending the fair and the books each
  one brings, imported from Excel.
- recommendation: links a member to an exhibition_book with a quantity.
  get_recommended_books_report() rolls these up across every vendor so the
  library can see just the fair books that were actually recommended.

The general book-catalog module (Manage Books) has been removed from this
build -- the app is scoped to the exhibition/recommendation workflow.

NOTE ON DATABASE ENGINE:
This module uses Python's built-in sqlite3 so the project runs immediately
with zero setup. The schema and queries are written in plain, portable SQL
so switching to MySQL later only requires swapping get_connection() for a
mysql.connector.connect(...) call and AUTOINCREMENT -> AUTO_INCREMENT.
"""

import sqlite3
import hashlib
from datetime import date

DB_NAME = "library.db"

MEMBER_ROLES = ("Student", "Faculty", "Researcher")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode()).hexdigest()


def init_db():
    """Create tables if they don't exist and seed a default admin account."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS admin (
        admin_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT UNIQUE NOT NULL,
        password      TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'Admin'
    );

    CREATE TABLE IF NOT EXISTS member (
        member_id         TEXT PRIMARY KEY,
        name              TEXT NOT NULL,
        email             TEXT UNIQUE,
        phone             TEXT,
        address           TEXT,
        role              TEXT NOT NULL DEFAULT 'Student',
        department        TEXT,
        designation       TEXT,
        membership_date   TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS vendor (
        vendor_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_name     TEXT NOT NULL,
        contact_person  TEXT,
        phone           TEXT,
        email           TEXT
    );

    CREATE TABLE IF NOT EXISTS exhibition_book (
        exhibition_book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id           INTEGER NOT NULL,
        title               TEXT NOT NULL,
        author              TEXT NOT NULL,
        subject             TEXT,
        isbn                TEXT,
        publisher           TEXT,
        category            TEXT,
        FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
    );

    CREATE TABLE IF NOT EXISTS recommendation (
        recommendation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        exhibition_book_id  INTEGER NOT NULL,
        member_id            TEXT NOT NULL,
        quantity              INTEGER NOT NULL DEFAULT 1,
        recommended_date      TEXT NOT NULL,
        FOREIGN KEY (exhibition_book_id) REFERENCES exhibition_book(exhibition_book_id),
        FOREIGN KEY (member_id) REFERENCES member(member_id)
    );
    """)

    # ---- migration: add designation to a member table created before this update
    member_cols = {row["name"] for row in cur.execute("PRAGMA table_info(member)").fetchall()}
    if "designation" not in member_cols:
        cur.execute("ALTER TABLE member ADD COLUMN designation TEXT")

    # Seed a default admin login if the table is empty
    cur.execute("SELECT COUNT(*) AS c FROM admin")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO admin (username, password, role) VALUES (?, ?, ?)",
            ("admin", hash_password("admin123"), "Admin"),
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------- AUTH ----
def verify_login(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM admin WHERE username = ? AND password = ?",
        (username, hash_password(password)),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# -------------------------------------------------------- MEMBER CRUD -----
def _blank_to_none(value):
    """Blank strings become NULL, so UNIQUE columns (email) never collide on ''."""
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def add_member(member_id, name, email, phone, address, role, department, designation=""):
    """
    member_id is entered by staff, not auto-generated -- students and
    faculty typically use different ID formats (STU101 vs an Emp ID), so
    this is a free-text primary key.
    Raises ValueError if the ID (or email) is already in use.
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO member (member_id, name, email, phone, address, role,
                                   department, designation, membership_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (member_id, name, _blank_to_none(email), _blank_to_none(phone),
             _blank_to_none(address), role, _blank_to_none(department),
             _blank_to_none(designation), date.today().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        if "member.member_id" in str(e) or "PRIMARY KEY" in str(e):
            raise ValueError(f"Member ID '{member_id}' is already in use.")
        if "member.email" in str(e):
            raise ValueError(f"Email '{email}' is already in use by another member.")
        raise ValueError("Could not add member (duplicate value).")
    conn.close()


def update_member(member_id, name, email, phone, address, role, department, designation=""):
    """The Member ID itself is not editable once created -- only the other fields."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE member SET name=?, email=?, phone=?, address=?, role=?,
                                 department=?, designation=?
               WHERE member_id=?""",
            (name, _blank_to_none(email), _blank_to_none(phone), _blank_to_none(address),
             role, _blank_to_none(department), _blank_to_none(designation), member_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Email '{email}' is already in use by another member.")
    conn.close()


def bulk_add_members(rows, role="Faculty"):
    """
    Import staff/faculty from parsed Excel rows (keys: member_id, name,
    designation, department, email -- as produced by
    excel_import.read_excel_rows).

    A row whose Emp ID already exists updates that person's name,
    designation, department and email instead of failing, so re-uploading
    a corrected sheet is safe.

    Returns (added, updated, skipped) where skipped is a list of
    (excel_row_number, reason) -- row 1 is the header, so data starts at 2.
    """
    conn = get_connection()
    cur = conn.cursor()
    added = updated = 0
    skipped = []
    for row_no, r in enumerate(rows, start=2):
        member_id = (r.get("member_id") or "").strip()
        name = (r.get("name") or "").strip()
        if not member_id or not name:
            skipped.append((row_no, "missing Emp ID or Name"))
            continue
        email = _blank_to_none(r.get("email"))
        department = _blank_to_none(r.get("department"))
        designation = _blank_to_none(r.get("designation"))
        exists = cur.execute(
            "SELECT 1 FROM member WHERE member_id = ?", (member_id,)
        ).fetchone()
        try:
            if exists:
                cur.execute(
                    """UPDATE member SET name=?, email=?, role=?, department=?, designation=?
                       WHERE member_id=?""",
                    (name, email, role, department, designation, member_id),
                )
                updated += 1
            else:
                cur.execute(
                    """INSERT INTO member (member_id, name, email, role, department,
                                           designation, membership_date)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (member_id, name, email, role, department, designation,
                     date.today().isoformat()),
                )
                added += 1
        except sqlite3.IntegrityError:
            skipped.append((row_no, f"email '{email}' is already used by another member"))
    conn.commit()
    conn.close()
    return added, updated, skipped


def delete_member(member_id):
    conn = get_connection()
    conn.execute("DELETE FROM member WHERE member_id = ?", (member_id,))
    conn.commit()
    conn.close()


def search_members(keyword="", role=None):
    """
    Search members, optionally narrowed to one role (Student / Faculty /
    Researcher). Passing role=None (or "All") returns every member.
    """
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{keyword}%"
    query = """SELECT * FROM member
               WHERE (member_id LIKE ? OR name LIKE ? OR email LIKE ? OR phone LIKE ?
                      OR department LIKE ? OR designation LIKE ?)"""
    params = [like] * 6
    if role and role != "All":
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY name"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_member(member_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM member WHERE member_id = ?", (member_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------- VENDOR CRUD --
def add_vendor(vendor_name, contact_person, phone, email):
    conn = get_connection()
    conn.execute(
        "INSERT INTO vendor (vendor_name, contact_person, phone, email) VALUES (?, ?, ?, ?)",
        (vendor_name, contact_person, phone, email),
    )
    conn.commit()
    conn.close()


def update_vendor(vendor_id, vendor_name, contact_person, phone, email):
    conn = get_connection()
    conn.execute(
        "UPDATE vendor SET vendor_name=?, contact_person=?, phone=?, email=? WHERE vendor_id=?",
        (vendor_name, contact_person, phone, email, vendor_id),
    )
    conn.commit()
    conn.close()


def delete_vendor(vendor_id):
    conn = get_connection()
    conn.execute("DELETE FROM vendor WHERE vendor_id = ?", (vendor_id,))
    conn.commit()
    conn.close()


def search_vendors(keyword=""):
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{keyword}%"
    cur.execute(
        "SELECT * FROM vendor WHERE vendor_name LIKE ? OR contact_person LIKE ? ORDER BY vendor_name",
        (like, like),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_vendor(vendor_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vendor WHERE vendor_id = ?", (vendor_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------- EXHIBITION BOOKS --
def bulk_add_exhibition_books(vendor_id, rows):
    """
    rows: list of dicts with keys title, author, subject, isbn, publisher, category
    (as produced by excel_import.read_excel_rows). Rows missing a title or
    author are skipped rather than raising, so one bad row doesn't sink
    an entire vendor's sheet.
    Returns (inserted_count, skipped_count).
    """
    conn = get_connection()
    cur = conn.cursor()
    inserted, skipped = 0, 0
    for r in rows:
        title = (r.get("title") or "").strip()
        author = (r.get("author") or "").strip()
        if not title or not author:
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO exhibition_book (vendor_id, title, author, subject, isbn, publisher, category)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (vendor_id, title, author, r.get("subject", ""), r.get("isbn", ""),
             r.get("publisher", ""), r.get("category", "")),
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted, skipped


def search_exhibition_books(keyword="", vendor_id=None):
    """Search books brought to the fair, optionally narrowed to one vendor."""
    conn = get_connection()
    cur = conn.cursor()
    like = f"%{keyword}%"
    query = """SELECT eb.*, v.vendor_name FROM exhibition_book eb
               JOIN vendor v ON eb.vendor_id = v.vendor_id
               WHERE (eb.title LIKE ? OR eb.author LIKE ? OR eb.isbn LIKE ?
                      OR eb.category LIKE ? OR eb.subject LIKE ?)"""
    params = [like, like, like, like, like]
    if vendor_id:
        query += " AND eb.vendor_id = ?"
        params.append(vendor_id)
    query += " ORDER BY eb.title"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_exhibition_book(exhibition_book_id):
    conn = get_connection()
    conn.execute("DELETE FROM exhibition_book WHERE exhibition_book_id = ?", (exhibition_book_id,))
    conn.commit()
    conn.close()


def clear_vendor_books(vendor_id):
    """Remove all exhibition books for a vendor -- used before deleting a vendor
    or before re-uploading a corrected sheet."""
    conn = get_connection()
    conn.execute("DELETE FROM exhibition_book WHERE vendor_id = ?", (vendor_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------- RECOMMEND ----
def add_recommendation(exhibition_book_id, member_id, quantity):
    conn = get_connection()
    conn.execute(
        """INSERT INTO recommendation (exhibition_book_id, member_id, quantity, recommended_date)
           VALUES (?, ?, ?, ?)""",
        (exhibition_book_id, member_id, quantity, date.today().isoformat()),
    )
    conn.commit()
    conn.close()


def _norm(text):
    return " ".join(str(text or "").lower().split())


def get_recommendation_rows(keyword="", vendor_id=None):
    """
    Raw recommendation lines (one per submitted line), joined with the book,
    its vendor and the recommender. Used by the merged report and by the
    admin copy's "Recommendation Details" sheet.
    """
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT r.recommendation_id, r.exhibition_book_id, r.quantity, r.recommended_date,
               eb.title, eb.author, eb.isbn, eb.publisher, eb.category,
               v.vendor_id, v.vendor_name,
               m.member_id, m.name AS member_name, m.role, m.designation, m.department
        FROM recommendation r
        JOIN exhibition_book eb ON r.exhibition_book_id = eb.exhibition_book_id
        JOIN vendor v ON eb.vendor_id = v.vendor_id
        JOIN member m ON r.member_id = m.member_id
    """
    params = []
    if vendor_id:
        query += " WHERE eb.vendor_id = ?"
        params.append(vendor_id)
    query += " ORDER BY eb.title, v.vendor_name, r.recommendation_id"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    kw = keyword.strip().lower()
    if kw:
        fields = ("title", "author", "isbn", "category", "vendor_name", "member_name")
        rows = [r for r in rows
                if kw in " ".join(str(r[f] or "") for f in fields).lower()]
    return rows


def _person_label(r):
    extra = ", ".join(x for x in (r["designation"], r["department"]) if x)
    return f"{r['member_name']} ({extra})" if extra else r["member_name"]


def get_recommended_books_report(keyword="", vendor_id=None):
    """
    The final module: one row per BOOK (not per vendor copy of the book).

    The same title + author offered by several vendors is merged into a
    single row whose Vendor column lists every vendor ("Vendor A, Vendor B"),
    so a faculty who picked the book from two vendors is not repeated.

    Quantity rule: each recommender counts once per book -- if they picked
    the same book from two vendors, the larger quantity is used (they want
    the book, and the vendors are alternatives). Different recommenders'
    quantities are added together.
    """
    books = {}
    for r in get_recommendation_rows(keyword, vendor_id):
        key = (_norm(r["title"]), _norm(r["author"]))
        b = books.setdefault(key, {
            "title": r["title"], "author": r["author"], "isbn": "",
            "publisher": "", "category": "",
            "vendors": [], "per_member": {}, "people": {},
        })
        for field in ("isbn", "publisher", "category"):
            if not b[field] and r[field]:
                b[field] = r[field]
        if r["vendor_name"] not in b["vendors"]:
            b["vendors"].append(r["vendor_name"])
        mid = r["member_id"]
        b["per_member"][mid] = max(b["per_member"].get(mid, 0), r["quantity"])
        b["people"][mid] = (r["member_name"], _person_label(r))

    result = []
    for b in books.values():
        people = sorted(b["people"].values(), key=lambda p: p[0].lower())
        result.append({
            "title": b["title"], "author": b["author"], "isbn": b["isbn"],
            "publisher": b["publisher"], "category": b["category"],
            "vendors": ", ".join(sorted(b["vendors"], key=str.lower)),
            "vendor_count": len(b["vendors"]),
            "total_quantity": sum(b["per_member"].values()),
            "recommender_count": len(people),
            "recommenders": ", ".join(p[0] for p in people),
            "recommender_details": "; ".join(p[1] for p in people),
        })
    result.sort(key=lambda x: (-x["total_quantity"], x["title"].lower()))
    return result


def get_vendor_copy_data():
    """
    One entry per vendor that has at least one recommended book, listing
    that vendor's books with the quantity requested from them. Recommender
    names are deliberately left out -- a vendor only needs what to supply.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT v.vendor_id, v.vendor_name, v.contact_person, v.phone, v.email,
                  eb.title, eb.author, eb.isbn, eb.publisher, eb.category,
                  SUM(r.quantity) AS quantity
           FROM recommendation r
           JOIN exhibition_book eb ON r.exhibition_book_id = eb.exhibition_book_id
           JOIN vendor v ON eb.vendor_id = v.vendor_id
           GROUP BY eb.exhibition_book_id
           ORDER BY v.vendor_name, eb.title"""
    )
    vendors = {}
    for r in cur.fetchall():
        entry = vendors.setdefault(r["vendor_id"], {
            "vendor": {"vendor_id": r["vendor_id"], "vendor_name": r["vendor_name"],
                       "contact_person": r["contact_person"], "phone": r["phone"],
                       "email": r["email"]},
            "items": [],
        })
        entry["items"].append({
            "title": r["title"], "author": r["author"], "isbn": r["isbn"],
            "publisher": r["publisher"], "category": r["category"],
            "quantity": r["quantity"],
        })
    conn.close()
    return list(vendors.values())
