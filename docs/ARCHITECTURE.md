# Libra — Kiến trúc dự án

Libra sử dụng Flask làm lớp HTTP, MySQL làm hệ quản trị cơ sở dữ liệu và chia nghiệp vụ theo mô hình repository/service.

```text
libra/
├── pyproject.toml
├── poetry.lock
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   └── ARCHITECTURE.md
├── migrations/
│   ├── schema.sql
│   └── versions/
│       └── 0002_complete_library_workflows.sql
├── scripts/
│   └── create_admin.py
├── tests/
│   └── unit/
│       └── test_core_rules.py
└── source/
    ├── app.py
    ├── configs/
    │   └── settings.py
    ├── core/
    │   ├── decorators.py
    │   ├── exceptions.py
    │   ├── money.py
    │   └── security.py
    ├── database/
    │   ├── connection.py
    │   ├── row_mapper.py
    │   └── transaction.py
    ├── domain/entities/
    │   ├── book.py
    │   ├── borrowing.py
    │   ├── reader.py
    │   └── user.py
    ├── repositories/
    │   ├── book_repository.py
    │   ├── borrowing_repository.py
    │   ├── fine_repository.py
    │   ├── reader_repository.py
    │   ├── report_repository.py
    │   └── return_repository.py
    ├── services/
    │   ├── account_service.py
    │   ├── auth_service.py
    │   ├── book_service.py
    │   ├── borrowing_service.py
    │   ├── fine_service.py
    │   ├── reader_service.py
    │   └── return_service.py
    ├── web/
    │   ├── routes/
    │   └── validators/
    ├── templates/
    │   ├── admin/
    │   ├── auth/
    │   ├── librarian/
    │   ├── reader/
    │   └── reports/
    └── static/
        ├── css/
        └── js/
```

## Trách nhiệm các lớp

- `source/app.py`: khởi tạo Flask, đăng ký blueprint, quản lý vòng đời kết nối database và xử lý lỗi HTTP.
- `source/configs/`: đọc cấu hình runtime từ biến môi trường và file `.env`.
- `source/core/`: hàm bảo mật, phân quyền, ngoại lệ nghiệp vụ và phép tính phí.
- `source/database/`: quản lý MySQL connection, transaction helper và ánh xạ bản ghi.
- `source/domain/entities/`: các đối tượng nghiệp vụ Book, Reader, User và BorrowingRecord.
- `source/repositories/`: câu lệnh SQL và thao tác lưu trữ; các thao tác nhiều bước có transaction.
- `source/services/`: xác thực đầu vào và điều phối use case.
- `source/web/routes/`: endpoint JSON và trang HTML được bảo vệ bằng session/role.
- `source/templates/` và `source/static/`: giao diện Jinja và JavaScript phía trình duyệt.
- `migrations/schema.sql`: schema khởi tạo MySQL mới, bao gồm bản sao vật lý và lịch sử thanh toán.
- `migrations/versions/`: migration nâng cấp database đã tạo từ schema cũ; cần sao lưu trước khi áp dụng.
- `tests/unit/`: kiểm thử logic thuần không cần MySQL.

## Quy tắc lưu trữ quan trọng

Một bản ghi trong `books` đại diện cho đầu sách; từng bản sao vật lý được lưu trong `book_copies`. Khi giảm số lượng, bản sao khả dụng được chuyển sang `RETIRED` thay vì xóa, nhờ đó không phá vỡ các khóa ngoại tới lịch sử mượn. `books.total_quantity` và `books.available_quantity` là số lượng bản sao còn lưu hành; bản sao `BORROWED`, `DAMAGED` hoặc `LOST` vẫn nằm trong tổng số bản sao đang lưu hành, còn `RETIRED` không được tính.

Các khoản phí được tính trên từng `borrowing_details`. Mỗi lần thanh toán được ghi riêng trong `fine_payments` để giữ lịch sử và hỗ trợ thanh toán từng phần.

## Vận hành

- Copy `.env.example` thành `.env` rồi cấu hình secret và kết nối MySQL. Không commit `.env`.
- Database mới: chạy `mysql -u root -p < migrations/schema.sql`.
- Database cũ từ phiên bản trước: sao lưu rồi chạy `mysql -u root -p library_db < migrations/versions/0002_complete_library_workflows.sql`; không chạy migration này trên database mới.
- Dùng `python scripts/create_admin.py` để tạo tài khoản quản trị đầu tiên.
- Chạy `python -m source.app` để khởi động web app.
- Chạy `python -m unittest discover -s tests -v` để chạy unit tests.
