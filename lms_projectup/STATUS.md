# Project Status — Book Exhibition Automation Update

**Project:** Library Management System — Book Exhibition Automation
**Scope:** Fully focused on the vendor/recommendation workflow (general
catalog and circulation modules removed)

| Module | Status | Notes |
|---|---|---|
| Database design (Member, Vendor, Exhibition_Book, Recommendation, Admin) | ✅ Done | Member ID is now a staff-entered TEXT primary key |
| Login / Authentication | ✅ Done | Unchanged |
| Manage Members | ✅ Done | Staff-entered Member ID, Role (Student/Faculty/Researcher), Department, role filter |
| Vendors & Exhibition (Excel upload) | ✅ Done | Vendor CRUD + bulk Excel import of Title/Author/Subject/ISBN/Publisher/Category |
| Recommend Books (Purchase Module) | ✅ Done | Member-ID lookup with auto-fill, accepts any ID format |
| Recommended Books (aggregated report) | ✅ Done | Cross-vendor rollup of everything actually recommended |
| Manage Books (general catalog) | ❌ Removed | Out of scope for this build |
| Issue / Return | ❌ Removed | Out of scope for this build |
| Reports | ❌ Removed | Out of scope for this build |

## What changed in this update
- **Member ID is now staff-entered**, not auto-numbered. Students and
  Faculty/Researchers can use their own ID conventions (e.g. `STU101`,
  `FAC204`). The ID is required when adding a member and locked (read-only)
  once that member exists, so it can't be accidentally changed later.
  Duplicate IDs are rejected with a clear error.
- **Manage Books removed entirely** — the sidebar item, the screen, and
  every related database function/table. The app now opens directly to
  Manage Members.
- **Recommend Books** updated to look up members by their (now
  alphanumeric) ID instead of assuming a numeric ID.

## What works right now (demo-ready)
- Secure login with hashed password storage
- Full CRUD + live search + role filter for Members, with a staff-chosen
  Member ID per role
- Vendor registration and bulk Excel import of their exhibition books
- Recommending books against a Member ID, with auto-filled Name/Department
- A live, searchable "Recommended Books" report aggregated across vendors

## Suggested additions (not yet built — see README for details)
- Designation (Faculty), Year/Semester (Student), Research Area (Researcher)
- Excel export of the Recommended Books report for procurement
- Auto-navigate to Recommended Books after a successful submission

## Latest update
- Manage Members: Student / Staff-Faculty / Researcher type, new **Designation** field, ordered columns,
  and **Upload Faculty Excel** (Emp ID, Name, Designation, Department, Email).
- Recommend Books: Designation now auto-fills with Name and Department.
- Recommended Books: the same book from several vendors is shown once ("Vendor A, Vendor B").
- New Excel exports: **Admin Copy** and one **Vendor Copy** per vendor.
- Fixed: two members with a blank email no longer clash; numeric/zero-padded Emp IDs are kept exactly.
