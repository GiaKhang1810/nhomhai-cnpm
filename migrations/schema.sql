
USE library_db;

-- ==========================================
-- 1. USERS
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    user_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    role ENUM('READER', 'LIBRARIAN', 'ADMIN') NOT NULL,

    account_status ENUM('ACTIVE', 'INACTIVE', 'LOCKED')
        NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_users_role (role),
    INDEX idx_users_status (account_status)
) ENGINE = InnoDB;


-- ==========================================
-- 2. LIBRARIANS
-- ==========================================

CREATE TABLE IF NOT EXISTS librarians (
    staff_id VARCHAR(20) PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),

    CONSTRAINT fk_librarians_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE = InnoDB;


-- ==========================================
-- 3. READERS
-- ==========================================

CREATE TABLE IF NOT EXISTS readers (
    reader_id VARCHAR(20) PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    dob DATE,
    gender ENUM('MALE', 'FEMALE', 'OTHER'),
    identity_number VARCHAR(20) NOT NULL UNIQUE,
    phone VARCHAR(20),

    card_issue_date DATE NOT NULL,
    card_expiry_date DATE NOT NULL,

    account_status ENUM('ACTIVE', 'INACTIVE', 'EXPIRED')
        NOT NULL DEFAULT 'ACTIVE',

    CONSTRAINT fk_readers_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_readers_card_dates
        CHECK (card_expiry_date >= card_issue_date)
) ENGINE = InnoDB;


-- ==========================================
-- 4. BOOKS
-- ==========================================

CREATE TABLE IF NOT EXISTS books (
    book_code VARCHAR(20) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100),
    publication_year INT,
    category VARCHAR(50),

    total_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    available_quantity INT UNSIGNED NOT NULL DEFAULT 0,

    listed_value DECIMAL(12, 2) NOT NULL,

    CONSTRAINT chk_books_quantity
        CHECK (available_quantity <= total_quantity),

    CONSTRAINT chk_books_value
        CHECK (listed_value >= 0),

    INDEX idx_books_title (title),
    INDEX idx_books_author (author),
    INDEX idx_books_category (category)
) ENGINE = InnoDB;


-- ==========================================
-- 5. BOOK COPIES
-- ==========================================

CREATE TABLE IF NOT EXISTS book_copies (
    copy_id VARCHAR(20) PRIMARY KEY,
    book_code VARCHAR(20) NOT NULL,

    `condition` VARCHAR(100),

    status ENUM('AVAILABLE', 'BORROWED', 'DAMAGED', 'LOST')
        NOT NULL DEFAULT 'AVAILABLE',

    CONSTRAINT fk_book_copies_book
        FOREIGN KEY (book_code)
        REFERENCES books(book_code)
        ON DELETE CASCADE,

    INDEX idx_book_copies_status (status)
) ENGINE = InnoDB;


-- ==========================================
-- 6. BORROWING RECORDS
-- ==========================================

CREATE TABLE IF NOT EXISTS borrowing_records (
    loan_id VARCHAR(20) PRIMARY KEY,
    reader_id VARCHAR(20) NOT NULL,

    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,

    status ENUM('BORROWED', 'RETURNED', 'OVERDUE')
        NOT NULL DEFAULT 'BORROWED',

    CONSTRAINT fk_borrowing_records_reader
        FOREIGN KEY (reader_id)
        REFERENCES readers(reader_id),

    CONSTRAINT chk_borrowing_dates
        CHECK (due_date >= borrow_date),

    INDEX idx_borrowing_reader (reader_id),
    INDEX idx_borrowing_status (status),
    INDEX idx_borrowing_due_date (due_date)
) ENGINE = InnoDB;


-- ==========================================
-- 7. BORROWING DETAILS
-- ==========================================

CREATE TABLE IF NOT EXISTS borrowing_details (
    detail_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    loan_id VARCHAR(20) NOT NULL,
    copy_id VARCHAR(20) NOT NULL,

    return_date DATE,

    overdue_fine DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    compensation DECIMAL(12, 2) NOT NULL DEFAULT 0.00,

    CONSTRAINT fk_borrowing_details_loan
        FOREIGN KEY (loan_id)
        REFERENCES borrowing_records(loan_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_borrowing_details_copy
        FOREIGN KEY (copy_id)
        REFERENCES book_copies(copy_id),

    CONSTRAINT chk_borrowing_fine
        CHECK (overdue_fine >= 0),

    CONSTRAINT chk_borrowing_compensation
        CHECK (compensation >= 0),

    INDEX idx_borrowing_details_copy (copy_id)
) ENGINE = InnoDB;
