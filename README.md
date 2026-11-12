# Libra — Library Management System

Hệ thống quản lý thư viện xây dựng bằng **Python 3.13+, Flask và MySQL**. Dự án tổ chức theo các lớp `domain`, `repositories`, `services` và `web` để tách biệt mô hình nghiệp vụ, truy cập dữ liệu, use case và HTTP endpoints.

## Chức năng

### Reader (Độc giả)
- Đăng nhập theo vai trò, tìm sách theo mã/tên/tác giả và xem chi tiết, số bản khả dụng.
- Xem bảng thông tin hồ sơ/thẻ độc giả và lịch sử mượn của chính tài khoản đang đăng nhập.

### Librarian (Thủ thư)
- Tạo, tìm kiếm, cập nhật và ngừng kinh doanh đầu sách. Khi thêm đầu sách, hệ thống tạo các bản sao vật lý tương ứng.
- Tạo và cập nhật hồ sơ độc giả; khóa thẻ khi độc giả không còn bản sao đang mượn.
- Lập phiếu mượn, ghi nhận trả một phần hoặc toàn bộ các bản sao.
- Tính phí trễ hạn **5.000 VND/ngày/bản sao**; tính bồi thường theo giá trị niêm yết đối với bản sao hỏng/mất.
- Ghi nhận thanh toán toàn phần hoặc một phần các khoản phí.

### Administrator (Quản trị viên)
- Xem dashboard thống kê từ dữ liệu thực tế.
- Tạo, cập nhật vai trò và khóa tài khoản nhân viên.
- Xem báo cáo hoạt động mượn/trả và phân bố bản sao theo thể loại.

## Yêu cầu môi trường

- Python `>=3.13`
- MySQL `8.0.16+` (các constraint `CHECK` được thực thi từ phiên bản này)
- Poetry 2.x (khuyến nghị)

## Cài đặt

1. Tạo môi trường ảo và cài dependency:

   ```bash
   poetry install
   ```

2. Tạo file `.env` từ mẫu:

   ```bash
   cp .env.example .env
   ```

   Tạo `SECRET_KEY` ngẫu nhiên bằng lệnh `python -c "import secrets; print(secrets.token_urlsafe(48))"`, sau đó điền `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` và `DB_NAME`. Tài khoản MySQL của ứng dụng chỉ cần quyền đọc/thêm/sửa/xóa dữ liệu.

3. Khởi tạo schema. File hiện tại tạo database mặc định `library_db`:

   ```bash
   mysql -u root -p < migrations/schema.sql
   ```

   Đặt `DB_NAME=library_db` trong `.env`. Nếu dùng tên database khác, sửa dòng `USE library_db;` trong script trước khi chạy. Lệnh này dành cho database mới.

   Nếu bạn đã khởi tạo database bằng schema cũ có trong phiên bản dự án trước, hãy sao lưu database rồi chạy migration nâng cấp thay vì chạy lại schema mới:

   ```bash
   mysqldump -u root -p library_db > library_db_backup.sql
   mysql -u root -p library_db < migrations/versions/0002_complete_library_workflows.sql
   ```

   Tạo tài khoản MySQL riêng cho ứng dụng (đăng nhập bằng tài khoản quản trị MySQL). Ví dụ với cấu hình `DB_HOST=127.0.0.1`:

   ```sql
   CREATE USER IF NOT EXISTS 'libra_app'@'127.0.0.1' IDENTIFIED BY 'replace-with-database-password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON library_db.* TO 'libra_app'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```

   Dùng cùng mật khẩu trong `DB_PASSWORD`. Nếu MySQL chạy trên máy chủ khác, thay host trong lệnh `CREATE USER` bằng host/IP phù hợp. Ứng dụng chỉ cần quyền CRUD trên schema; không nên dùng tài khoản `root` để chạy web server.

4. Tạo tài khoản Administrator đầu tiên:

   ```bash
   poetry run python scripts/create_admin.py
   ```

   Script yêu cầu username, email và password; mật khẩu được hash trước khi lưu.

5. Chạy ứng dụng:

   ```bash
   poetry run python -m source.app
   ```

   Mở `http://127.0.0.1:5000`.

## Luồng nghiệp vụ quan trọng

### Tạo đầu sách

Một dòng `books` là đầu sách; mỗi bản sao vật lý được lưu riêng trong `book_copies`. Khi tạo sách với số lượng `N`, ứng dụng ghi một bản ghi `books` và `N` bản ghi `book_copies` trong cùng transaction. Không thể lập phiếu mượn chỉ dựa trên số lượng tổng hợp.

### Mượn sách

Trong transaction, ứng dụng khóa dòng độc giả, kiểm tra thẻ còn hiệu lực, số lượng đang mượn dưới 5, không có sách quá hạn; sau đó khóa các đầu sách/bản sao được chọn, xác minh tất cả bản sao ở trạng thái `AVAILABLE`, ghi phiếu và chi tiết, cập nhật trạng thái bản sao và số lượng khả dụng. Nếu một bước thất bại, toàn bộ transaction rollback.

### Trả sách và thanh toán

Mỗi chi tiết phiếu mượn được liên kết với đúng một `copy_id`. Hệ thống chỉ nhận trả bản sao thuộc phiếu và chưa trả trước đó. Bản sao bình thường trở lại `AVAILABLE`; bản sao hỏng/mất chuyển sang trạng thái tương ứng và không tăng số lượng khả dụng. Khi giảm số lượng đầu sách, các bản sao khả dụng được chuyển sang `RETIRED` thay vì xóa, để bảo toàn khóa ngoại và lịch sử giao dịch. Phí phát sinh lưu trong `borrowing_details`; các lần thanh toán lưu riêng trong `fine_payments` để hỗ trợ thanh toán từng phần và tránh ghi đè lịch sử.

## API chính

| Method | Endpoint | Vai trò | Mô tả |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Đăng nhập; payload gồm `username`, `password`, `role` (`reader`, `librarian`, `admin`) |
| `POST` | `/auth/logout` | Authenticated | Đăng xuất |
| `GET` | `/api/books/?q=` | All roles | Danh mục/tìm kiếm sách |
| `GET` | `/api/books/<book_code>` | All roles | Chi tiết sách |
| `POST` | `/api/books/` | Librarian/Admin | Thêm đầu sách và bản sao |
| `PUT` / `DELETE` | `/api/books/<book_code>` | Librarian/Admin | Cập nhật/ngừng kinh doanh |
| `GET` | `/api/readers/search?q=` | Librarian/Admin | Tìm độc giả |
| `POST` / `PUT` | `/api/readers/` / `/api/readers/<reader_id>` | Librarian/Admin | Tạo/cập nhật độc giả |
| `PATCH` | `/api/readers/<reader_id>/deactivate` | Librarian/Admin | Khóa thẻ độc giả |
| `POST` | `/borrowing/create` | Librarian | Tạo phiếu mượn; `reader_id`, `copy_ids[]` |
| `GET` | `/borrowing/lookup/<loan_id>` | Librarian | Tra cứu phiếu mượn và các bản sao |
| `GET` | `/borrowing/lookup?reader_id=<reader_id>` | Librarian | Tra cứu danh sách phiếu mượn theo độc giả |
| `POST` | `/returns/process` | Librarian | Ghi nhận trả; `loan_id`, `items[{copy_id, condition}]` |
| `GET` | `/api/fines/outstanding` | Librarian/Admin | Các khoản phí chưa thanh toán; có thể lọc `reader_id` |
| `POST` | `/api/fines/payments` | Librarian | Ghi nhận thanh toán; `detail_id`, `amount`, `payment_method` |
| `GET` | `/profile/api/me` | Reader | Hồ sơ của chính độc giả đăng nhập |
| `GET` | `/profile/api/history` | Reader | Lịch sử mượn của chính độc giả đăng nhập |
| `GET` | `/admin/reports/activity?days=7` | Librarian/Admin | Thống kê mượn/trả theo ngày |
| `GET` | `/admin/reports/categories` | Librarian/Admin | Phân bố bản sao theo thể loại |
| `GET` | `/api/accounts/` | Admin | Danh sách tài khoản nhân viên |
| `POST` / `PUT` | `/api/accounts/` / `/api/accounts/<user_id>` | Admin | Tạo/cập nhật nhân viên và vai trò |
| `PATCH` | `/api/accounts/<user_id>/deactivate` | Admin | Khóa tài khoản nhân viên |

Các endpoint JSON trả về dạng `{ "success": boolean, "message"?: string, "data"?: ... }`. Quyền luôn được xác minh ở backend, không dựa vào tab vai trò phía giao diện.

## Cấu trúc thư mục

```text
libra/
├── docs/                    # Tài liệu kiến trúc
├── migrations/              # MySQL schema và migration nâng cấp
│   └── versions/            # Các phiên bản nâng cấp schema đã phát hành
├── scripts/                 # Công cụ quản trị (tạo admin)
├── source/
│   ├── app.py               # Flask application factory
│   ├── configs/             # Cấu hình từ environment
│   ├── core/                # Security, decorators, business helpers
│   ├── database/            # Connection, transaction, row mapping
│   ├── domain/entities/     # Domain entities
│   ├── repositories/        # SQL và persistence
│   ├── services/            # Use cases và business rules
│   ├── web/routes/          # HTTP routes
│   ├── templates/           # Jinja templates theo vai trò
│   └── static/              # CSS/JavaScript
└── tests/unit/              # Unit tests
```

## Kiểm thử

Chạy kiểm thử quy tắc thuần Python bằng:

```bash
poetry run python -m unittest discover -s tests -v
```

Các luồng cần kiểm thử tích hợp với MySQL gồm đăng nhập, tạo đầu sách/bản sao, mượn và trả đồng thời, thanh toán từng phần, phân quyền và báo cáo. Các kiểm thử tích hợp này cần một MySQL instance được khởi tạo từ `migrations/schema.sql`.

## Lưu ý vận hành và bảo mật

- Không commit `.env`; chỉ commit `.env.example`.
- Mật khẩu được hash bằng Werkzeug; không lưu mật khẩu thô.
- Truy vấn SQL dùng parameterized queries. Chỉ phần số lượng placeholder `IN (...)` được tạo động từ số phần tử đầu vào; dữ liệu vẫn được bind qua tham số.
- Cookie session đặt `HttpOnly` và `SameSite=Lax`; bật `SESSION_COOKIE_SECURE=true` khi chạy sau HTTPS.
- Ứng dụng chưa cung cấp luồng quên mật khẩu/email, yêu cầu đặt trước sách, điểm thưởng, thông báo hoặc yêu thích vì các chức năng này không nằm trong schema/nghiệp vụ bắt buộc của tài liệu đặc tả hiện tại.
- Dashboard hiển thị dữ liệu lấy từ MySQL; cần khởi tạo database và có dữ liệu trước khi sử dụng.
