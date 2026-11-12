-- Libra - initial schema (MySQL 8.0.16+)
-- Create the database once, then run this file with the selected schema.
CREATE DATABASE IF NOT EXISTS library_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE library_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('READER', 'LIBRARIAN', 'ADMIN') NOT NULL,
    account_status ENUM('ACTIVE', 'INACTIVE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (account_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS librarians (
    staff_id VARCHAR(20) PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    CONSTRAINT fk_librarians_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

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
    account_status ENUM('ACTIVE', 'INACTIVE', 'EXPIRED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_readers_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_readers_card_dates CHECK (card_expiry_date >= card_issue_date),
    INDEX idx_readers_name (full_name),
    INDEX idx_readers_status (account_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS books (
    book_code VARCHAR(20) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100),
    publication_year SMALLINT UNSIGNED,
    category VARCHAR(80),
    listed_value DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    available_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_books_quantity CHECK (available_quantity <= total_quantity),
    CONSTRAINT chk_books_value CHECK (listed_value >= 0),
    CONSTRAINT chk_books_year CHECK (publication_year IS NULL OR publication_year BETWEEN 1000 AND 9999),
    INDEX idx_books_title (title),
    INDEX idx_books_author (author),
    INDEX idx_books_category (category),
    INDEX idx_books_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS book_copies (
    copy_id VARCHAR(20) PRIMARY KEY,
    book_code VARCHAR(20) NOT NULL,
    `condition` ENUM('NORMAL', 'DAMAGED', 'LOST') NOT NULL DEFAULT 'NORMAL',
    status ENUM('AVAILABLE', 'BORROWED', 'DAMAGED', 'LOST', 'RETIRED') NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_book_copies_book FOREIGN KEY (book_code)
        REFERENCES books(book_code) ON DELETE RESTRICT,
    INDEX idx_book_copies_book_status (book_code, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS borrowing_records (
    loan_id VARCHAR(20) PRIMARY KEY,
    reader_id VARCHAR(20) NOT NULL,
    borrow_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('BORROWED', 'RETURNED', 'OVERDUE') NOT NULL DEFAULT 'BORROWED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_borrowing_records_reader FOREIGN KEY (reader_id)
        REFERENCES readers(reader_id) ON DELETE RESTRICT,
    CONSTRAINT chk_borrowing_dates CHECK (due_date >= borrow_date),
    INDEX idx_borrowing_reader_date (reader_id, borrow_date),
    INDEX idx_borrowing_status_due (status, due_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS borrowing_details (
    detail_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    loan_id VARCHAR(20) NOT NULL,
    copy_id VARCHAR(20) NOT NULL,
    return_date DATE,
    overdue_fine DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    compensation DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_borrowing_details_loan FOREIGN KEY (loan_id)
        REFERENCES borrowing_records(loan_id) ON DELETE CASCADE,
    CONSTRAINT fk_borrowing_details_copy FOREIGN KEY (copy_id)
        REFERENCES book_copies(copy_id) ON DELETE RESTRICT,
    CONSTRAINT chk_borrowing_fine CHECK (overdue_fine >= 0),
    CONSTRAINT chk_borrowing_compensation CHECK (compensation >= 0),
    UNIQUE KEY uq_borrowing_loan_copy (loan_id, copy_id),
    INDEX idx_borrowing_details_copy (copy_id),
    INDEX idx_borrowing_details_return (return_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fine_payments (
    payment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    detail_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL DEFAULT 'CASH',
    paid_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    received_by INT UNSIGNED NOT NULL,
    note VARCHAR(255),
    CONSTRAINT fk_fine_payments_detail FOREIGN KEY (detail_id)
        REFERENCES borrowing_details(detail_id) ON DELETE RESTRICT,
    CONSTRAINT fk_fine_payments_user FOREIGN KEY (received_by)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT chk_fine_payment_amount CHECK (amount > 0),
    INDEX idx_fine_payments_detail (detail_id),
    INDEX idx_fine_payments_paid_at (paid_at)
) ENGINE=InnoDB;
