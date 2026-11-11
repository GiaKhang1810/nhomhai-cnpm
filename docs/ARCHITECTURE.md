# Libra -- Project Structure

``` text
libra/
├── pyproject.toml
├── poetry.lock
├── README.md
├── .env
├── .env.example
├── .gitignore
│
├── migrations/
│   ├── versions/
│   └── schema.sql
│
├── source/
│   ├── __init__.py
│   ├── app.py
│   ├── extensions.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── decorators.py
│   │   └── constants.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── transaction.py
│   │   └── row_mapper.py
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   ├── enums/
│   │   ├── rules/
│   │   └── interfaces/
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── book_repository.py
│   │   ├── reader_repository.py
│   │   ├── book_copy_repository.py
│   │   ├── loan_repository.py
│   │   ├── return_repository.py
│   │   ├── fine_repository.py
│   │   ├── account_repository.py
│   │   └── report_repository.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── book_service.py
│   │   ├── reader_service.py
│   │   ├── borrowing_service.py
│   │   ├── return_service.py
│   │   ├── fine_service.py
│   │   ├── account_service.py
│   │   └── report_service.py
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── middleware.py
│   │   ├── errors.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── books.py
│   │   │   ├── readers.py
│   │   │   ├── borrowing.py
│   │   │   ├── returns.py
│   │   │   ├── fines.py
│   │   │   ├── accounts.py
│   │   │   ├── reports.py
│   │   │   └── profile.py
│   │   │
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── book_validator.py
│   │       ├── reader_validator.py
│   │       └── borrowing_validator.py
│   │
│   ├── templates/
│   │   ├── layouts/
│   │   ├── components/
│   │   ├── auth/
│   │   ├── reader/
│   │   ├── librarian/
│   │   ├── admin/
│   │   └── errors/
│   │
│   └── static/
│       ├── css/
│       ├── js/
│       ├── images/
│       └── fonts/
│
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_auth_service.py
    │   ├── test_borrowing_service.py
    │   ├── test_return_service.py
    │   └── test_fine_service.py
    │
    ├── integration/
    │   ├── test_book_repository.py
    │   └── test_loan_repository.py
    │
    └── functional/
        ├── test_auth_routes.py
        ├── test_book_routes.py
        └── test_borrowing_routes.py
```

## Directory responsibilities

  -----------------------------------------------------------------------
  Path                                Responsibility
  ----------------------------------- -----------------------------------
  `migrations/`                       Database schema and migration
                                      history.

  `source/app.py`                     Flask application factory and
                                      application setup.

  `source/extensions.py`              Shared Flask extensions and
                                      initialized integrations.

  `source/config/`                    Application settings and logging
                                      configuration.

  `source/core/`                      Cross-cutting concerns such as
                                      security, permissions, exceptions,
                                      and constants.

  `source/database/`                  MySQL connection management,
                                      transactions, and row mapping using
                                      `mysql-connector-python`.

  `source/domain/`                    Domain entities, enums, business
                                      rules, and interfaces.

  `source/repositories/`              SQL access and persistence
                                      operations.

  `source/services/`                  Application use cases and business
                                      workflows.

  `source/web/`                       HTTP middleware, error handling,
                                      routes, and request validation.

  `source/templates/`                 Jinja templates grouped by layout
                                      and user role.

  `source/static/`                    CSS, JavaScript, images, and fonts.

  `tests/`                            Unit, integration, and functional
                                      tests.
  -----------------------------------------------------------------------

## Notes

-   Keep secrets in `.env`; commit `.env.example` with placeholder
    values only.
-   Keep database schema changes in `migrations/`. Avoid modifying an
    already-applied migration; create a new migration instead.
-   Keep SQL and persistence logic in repositories. Services should
    coordinate use cases and transactions.
-   Keep password hashing and verification in `source/core/security.py`,
    using Flask's Werkzeug security utilities.
-   Use parameterized queries with `mysql-connector-python`; never
    interpolate user input into SQL strings.
-   The `schema.sql` file can serve as the initial database schema. If a
    migration tool is adopted, use it as the source of versioned schema
    changes.
