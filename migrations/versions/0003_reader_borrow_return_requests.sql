-- Libra migration 0003: reader borrowing and return requests, plus loan management workflow.
-- Run once against the existing library_db database. This migration is additive and preserves data.
USE library_db;

CREATE TABLE IF NOT EXISTS borrow_requests (
    request_id VARCHAR(24) PRIMARY KEY,
    reader_id VARCHAR(20) NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    processed_by INT UNSIGNED NULL,
    staff_note VARCHAR(500),
    CONSTRAINT fk_borrow_requests_reader FOREIGN KEY (reader_id)
        REFERENCES readers(reader_id) ON DELETE RESTRICT,
    CONSTRAINT fk_borrow_requests_processor FOREIGN KEY (processed_by)
        REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_borrow_requests_reader_status (reader_id, status),
    INDEX idx_borrow_requests_status_date (status, requested_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS borrow_request_items (
    request_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(24) NOT NULL,
    book_code VARCHAR(20) NOT NULL,
    quantity TINYINT UNSIGNED NOT NULL DEFAULT 1,
    CONSTRAINT fk_borrow_request_items_request FOREIGN KEY (request_id)
        REFERENCES borrow_requests(request_id) ON DELETE CASCADE,
    CONSTRAINT fk_borrow_request_items_book FOREIGN KEY (book_code)
        REFERENCES books(book_code) ON DELETE RESTRICT,
    CONSTRAINT chk_borrow_request_quantity CHECK (quantity BETWEEN 1 AND 5),
    UNIQUE KEY uq_borrow_request_book (request_id, book_code),
    INDEX idx_borrow_request_items_book (book_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS return_requests (
    return_request_id VARCHAR(24) PRIMARY KEY,
    reader_id VARCHAR(20) NOT NULL,
    detail_id BIGINT UNSIGNED NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    processed_by INT UNSIGNED NULL,
    staff_note VARCHAR(500),
    CONSTRAINT fk_return_requests_reader FOREIGN KEY (reader_id)
        REFERENCES readers(reader_id) ON DELETE RESTRICT,
    CONSTRAINT fk_return_requests_detail FOREIGN KEY (detail_id)
        REFERENCES borrowing_details(detail_id) ON DELETE RESTRICT,
    CONSTRAINT fk_return_requests_processor FOREIGN KEY (processed_by)
        REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_return_requests_reader_status (reader_id, status),
    INDEX idx_return_requests_status_date (status, requested_at),
    INDEX idx_return_requests_detail_status (detail_id, status)
) ENGINE=InnoDB;
