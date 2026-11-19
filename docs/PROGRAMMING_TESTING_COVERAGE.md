# Programming & Testing Coverage — Libra

This document records how the implementation maps to the existing submitted specification. It supplements the project; it does not replace or modify `SPECIFICATION.md`.

## Programming coverage

| Specification area | Implementation | GUI / entry point |
|---|---|---|
| Log In | `source/services/auth_service.py`, `source/domain/entities/user.py` | `source/templates/auth/login.html` |
| Search for Books / View Book Details | `source/services/book_service.py`, `source/repositories/book_repository.py`, `source/web/routes/books.py` | Reader catalogue and Librarian book management |
| Manage Books | `Book`, `BookCopy`, `BookService`, `BookRepository` | `source/templates/librarian/books.html` |
| Manage Readers | `Reader`, `ReaderService`, `ReaderRepository` | `source/templates/librarian/readers.html` |
| View Borrowing History / Personal Profile | `Reader.view_profile()`, `Reader.view_borrowing_history()`, profile routes | Reader dashboard, history and loans pages |
| Process Borrowing | `BorrowingRecord`, `BorrowingDetail`, `BorrowingService`, `BorrowingRepository` | Librarian borrow/loan workflow and Reader borrow requests |
| Process Returns | `BorrowingDetail.calculate_fine()`, `BookCopy.update_status()`, `ReturnService`, `ReturnRepository` | `source/templates/librarian/returns.html` |
| Manage Fines and Compensation | `FineService`, `FineRepository`, transaction-level return charge calculation | `source/templates/librarian/fines.html` |
| Manage Staff Accounts | `Administrator`, `AccountService`, account routes | `source/templates/admin/accounts.html` |
| Generate Reports | `Administrator.generate_reports()`, `ReportRepository` | Admin dashboard and report dashboard |

## Domain model additions

The original domain package did not explicitly define all entities named in the submitted Class Diagram. It now includes:

- `User`: includes a `login()` entry point that delegates to `AuthService`.
- `Reader`: includes `view_profile()` and reader-scoped `view_borrowing_history()`.
- `Librarian`: represents the staff profile and delegates book, reader, borrowing, return and fine use cases to their services.
- `Administrator`: maps `admin_id` to `users.user_id` in the current schema; delegates staff-account management and report generation.
- `Book`: validates mutable catalogue values and models activate/deactivate operations.
- `BookCopy`: validates physical-copy status and condition changes.
- `BorrowingRecord` / `BorrowingDetail`: models loan details, duplicate-copy prevention, return completion, overdue fines and damaged/lost-copy compensation.

The return repository now uses `BorrowingDetail.calculate_fine()` and `BookCopy.update_status()` inside the existing database transaction. The application remains layered as domain → service → repository → database; domain entities do not issue SQL themselves.

## GUI coverage

The project already contains role-based Flask/Jinja interfaces and browser-side JavaScript under `source/templates/` and `source/static/`. The templates include login, Reader catalogue/dashboard/history/loans, Librarian book/reader/borrow/loan/return/fine workspaces, and Administrator dashboard/account management. The specification file was left unchanged.

## Automated tests

Run from the project root after installing project dependencies:

```bash
poetry install
poetry run python -m unittest discover -s tests -v
```

The pure-Python suite covers borrowing validation, overdue-fine rules, entity invariants, book-copy state transitions, reader profile/history scoping, Librarian/Administrator service delegation and report aggregation. Web access-control tests are included and require Flask dependencies from `poetry install`.

Database integration tests involving MySQL (real login, concurrent loans/returns, persistence, fine-payment transactions and live report queries) still require a configured MySQL instance. They must be executed against a test database before claiming full integration-test completion.

## Test document

`docs/TESTING_DOCUMENT.xlsx` is populated in the original lecturer-supplied template. Its original sheet name, five columns and header text are preserved. It contains 48 planned test cases spanning all 12 use cases in `SPECIFICATION.md`. The workbook records expected outcomes only; it does not claim tests were executed.
