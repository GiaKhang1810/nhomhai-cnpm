-- Upgrade the original Libra schema created by the previous project version.
-- Run this only against an existing database created from the old schema.sql.
-- New installations must run migrations/schema.sql instead.

USE library_db;

ALTER TABLE users
    ADD COLUMN updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE readers
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE books
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Preserve known damage/loss states and normalize free-text legacy values.
UPDATE book_copies
SET `condition` = CASE
    WHEN status = 'DAMAGED' OR UPPER(COALESCE(`condition`, '')) = 'DAMAGED' THEN 'DAMAGED'
    WHEN status = 'LOST' OR UPPER(COALESCE(`condition`, '')) = 'LOST' THEN 'LOST'
    ELSE 'NORMAL'
END;

ALTER TABLE book_copies
    MODIFY COLUMN `condition` ENUM('NORMAL', 'DAMAGED', 'LOST') NOT NULL DEFAULT 'NORMAL',
    MODIFY COLUMN status ENUM('AVAILABLE', 'BORROWED', 'DAMAGED', 'LOST', 'RETIRED')
        NOT NULL DEFAULT 'AVAILABLE',
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    DROP FOREIGN KEY fk_book_copies_book,
    ADD CONSTRAINT fk_book_copies_book FOREIGN KEY (book_code)
        REFERENCES books(book_code) ON DELETE RESTRICT,
    ADD INDEX idx_book_copies_book_status (book_code, status);

ALTER TABLE borrowing_records
    ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD INDEX idx_borrowing_reader_date (reader_id, borrow_date),
    ADD INDEX idx_borrowing_status_due (status, due_date);

ALTER TABLE borrowing_details
    MODIFY COLUMN detail_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ADD UNIQUE KEY uq_borrowing_loan_copy (loan_id, copy_id),
    ADD INDEX idx_borrowing_details_return (return_date);

ALTER TABLE readers
    ADD INDEX idx_readers_name (full_name),
    ADD INDEX idx_readers_status (account_status);

ALTER TABLE books
    ADD INDEX idx_books_active (is_active);

CREATE TABLE fine_payments (
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

-- Reconcile active loans with physical copy states before rebuilding inventory.
UPDATE book_copies bc
JOIN borrowing_details bd ON bd.copy_id = bc.copy_id
SET bc.status = 'BORROWED'
WHERE bd.return_date IS NULL;

-- Older builds did not create physical copies when a title was inserted.
-- Backfill any missing copy rows so each book's total quantity has a physical ledger.
SET @libra_max_book_quantity = (SELECT COALESCE(MAX(total_quantity), 0) FROM books);
SET SESSION cte_max_recursion_depth = GREATEST(@libra_max_book_quantity, 1000);

INSERT INTO book_copies (copy_id, book_code, `condition`, status)
WITH RECURSIVE sequence_numbers(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM sequence_numbers WHERE n < @libra_max_book_quantity
), existing_copies AS (
    SELECT book_code, COUNT(*) AS copy_count
    FROM book_copies
    GROUP BY book_code
)
SELECT CONCAT('CP-', UPPER(SUBSTRING(REPLACE(UUID(), '-', ''), 1, 17))),
       b.book_code, 'NORMAL', 'AVAILABLE'
FROM books b
LEFT JOIN existing_copies ec ON ec.book_code = b.book_code
JOIN sequence_numbers seq
  ON seq.n <= GREATEST(b.total_quantity - COALESCE(ec.copy_count, 0), 0);

-- Retain existing copies if the legacy ledger already exceeds the recorded total.
UPDATE books b
SET b.total_quantity = GREATEST(
        b.total_quantity,
        (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_code = b.book_code)
    );

-- Recalculate the materialized availability count from the physical copy ledger.
UPDATE books b
SET b.available_quantity = (
    SELECT COUNT(*)
    FROM book_copies bc
    WHERE bc.book_code = b.book_code AND bc.status = 'AVAILABLE'
);
