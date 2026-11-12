# LIBRARY MANAGEMENT SYSTEM

## 1. FUNCTIONAL REQUIREMENTS

The Library Management System supports the daily operations of a small library. The system is organized into six main functions:

### 1.1 Book Management
- Readers can search for books by title, author, or book code and view basic availability information.
- Librarians and Administrators can view, add, update, and remove book records.
- A book record contains: book code, title, author, publisher, publication year, category, total quantity, and available quantity.

### 1.2 Reader Management
- Librarians can create, search, update, and deactivate reader records.
- A reader record contains: reader ID, full name, date of birth, gender, identity number, phone number, card issue date, card expiry date, and account status.

### 1.3 Borrowing Management
- Librarians create a borrowing record for a reader and select the book copies to be borrowed.
- Before confirming a loan, the system checks that:
  - The reader card is active.
  - The reader has fewer than five books currently borrowed.
  - The reader has no overdue unreturned books.
  - The requested copies are available.
- A borrowing record stores its ID, reader, borrowed book copies, borrowing date, due date, and status. The default borrowing period is 14 days.
- After a successful loan, the system decreases the available quantity of the relevant books.

### 1.4 Return and Fine Management
- Librarians search for a loan by loan ID or reader ID and record the returned book copies.
- The system compares the actual return date with the due date. The overdue fine is **5,000 VND** per day per copy.
- For a lost or damaged copy, the librarian records the condition and the system calculates compensation based on the listed book value.
- After confirmation, the system updates the loan and copy statuses and increases available quantity for copies that can be borrowed again.

### 1.5 Account and Access Management
- Readers, Librarians, and Administrators log in using a username or email and password.
- The system grants access according to the user role:
  - Readers can view only their own profile and borrowing history.
  - Administrators can create, update, deactivate, and assign roles to staff accounts.

### 1.6 Reports and Statistics
- Librarians and Administrators can view the total number of book titles, total book copies, and copies currently on loan.
- Reports include active readers, newly registered readers, borrowing and return counts over time, and overdue loans.

---

## 2. NON-FUNCTIONAL REQUIREMENTS

### 2.1 Usability
- The system interface should be easy to use on standard web browsers like Chrome and Edge. It should display well on screens with at least **1366x768** resolution.
- When users input missing or wrong data, the system must show a clear error message right next to the field (for example, *"Reader ID is missing"*) so they can fix it easily.

### 2.2 Reliability
- Database operations for borrowing or returning books must be handled as a single transaction. This prevents data errors or duplicate records if something goes wrong during the process.
- The system needs to be stable and work **99%** of the time during the library's operating hours.

### 2.3 Performance
- Searching for a book (by title, author, or code) should be fast and show results within **2 seconds**.
- Actions like creating a loan, returning a book, or paying fines must take less than **1 second** to process.

### 2.4 Security
- User passwords must be hashed before saving to the database. Plain text passwords are never saved.
- The code must use parameterized queries to prevent SQL Injection attacks. User inputs also need to be checked to prevent XSS.
- The system must check user roles properly. A reader can only view their own profile and borrowing history, not other people's data.

### 2.5 Technology Constraints
- The backend application is developed using Python with the Flask web framework.
- The database is designed and stored in MySQL.
- The source code and version history are managed on GitHub.

---

## 3. DATA FLOW DIAGRAMS (DFD)

### Level 0 (Context Diagram)
- **Reader**: Login, Search, View requests $\leftrightarrow$ Access, Info
- **Librarian**: Loan, fine calculations $\leftrightarrow$ Reports
- **Administrator**: Manage Accounts, Reports

### Level 1 Process Summary
- **1.0 Reader Management**: Processes reader registration and updates, interacting with Reader Profile storage.
- **2.0 Book Management**: Manages book collections and metadata.
- **3.0 Search for Books**: Handles book search requests and looks up book collections.
- **4.0 Loan and Repayment Management**: Verifies reader profile, updates book copies, and saves Loan/Return Slips.
- **5.0 Statistics and Reports**: Generates statistical reports based on system data.
- **6.0 Account Management**: Validates employee credentials, login data, and account updates.

---

## 4. USE CASE SPECIFICATIONS

### 4.1 List of Actors
| STT | Actor | Role Description |
| :--- | :--- | :--- |
| 1 | Reader | Search, view borrowing history |
| 2 | Librarian | Managing books and readers, and handling the borrowing, returning, and fining processes |
| 3 | Administrator | Account management |

### 4.2 List of Use Cases
| STT | Use-Case | Function Description |
| :--- | :--- | :--- |
| 1 | Log In | Log in to the system |
| 2 | Search for Books | Search catalogue by title, author, or code |
| 3 | View Book Details | View book info and availability |
| 4 | Manage Books | Add, update, or deactivate books |
| 5 | Manage Readers | Manage reader profiles and card status |
| 6 | View Borrowing History | View own borrowing records |
| 7 | Process Borrowing | Check conditions and create loans |
| 8 | Process Returns | Record returns and update statuses |
| 9 | Manage Fines and Compensation | Calculate and record fine payments |
| 10 | Manage Staff Accounts | Employee account management |
| 11 | Generate Reports | Display system reports |
| 12 | View Personal Profile | View own profile and card info |

---

## 5. CLASS DIAGRAM ENTITIES
- **User**: username, email, passwordHash, accountStatus, role (`login()`)
- **Reader**: readerID, fullName, dob, gender, identityNumber, phone, cardIssueDate, cardExpiryDate (`viewBorrowingHistory()`, `viewProfile()`)
- **Librarian**: staffID (`manageBooks()`, `manageReaders()`, `processBorrowing()`, `processReturns()`, `manageFines()`)
- **Administrator**: adminID (`manageStaffAccounts()`, `generateReports()`)
- **Book**: bookCode, title, author, publisher, publicationYear, category, totalQuantity, availableQuantity, listedValue (`updateBook()`, `deactivate()`)
- **BookCopy**: copyID, condition, status (`updateStatus()`)
- **BorrowingRecord**: loanID, borrowingDate, dueDate, status
- **BorrowingDetail**: returnDate, overdueFine, compensation (`calculateFine()`)

---

## 6. DATA MODEL (DATABASE SCHEMA)
- **`User`**: `UserID` (PK), `username`, `email`, `password_hash`, `role`, `accountStatus`
- **`librarian`**: `staffID` (PK), `fullName`, `phone`, `userID` (FK)
- **`Reader`**: `readerID` (PK), `fullName`, `dob`, `gender`, `identityNumber`, `phone`, `cardissueDate`, `cardExpiryDate`, `accountStatus`, `userID` (FK)
- **`Book`**: `bookCode` (PK), `title`, `author`, `publisher`, `publicationYear`, `category`, `availableQuantity`, `listedValue`
- **`BookCopy`**: `copyID` (PK), `Condition`, `status`, `BookCode` (FK)
- **`BorrowingRecord`**: `loanID` (PK), `borrowDate`, `dueDate`, `status`, `readerID` (FK)
- **`BorrowingDetail`**: `detailID` (PK), `returnDate`, `overdueFine`, `compensation`, `loanID` (FK), `copyID` (FK)

---

## 7. INTERFACE DESIGN DESCRIPTION

### 7.1 Login Interface
- Divided into a branding banner on the left ("Libra - Quản lý thư viện dễ dàng hơn") and a login form on the right.
- Role selection tabs: "Thủ thư" (Librarian), "Độc giả" (Reader), and "Quản trị viên" (Administrator).
- Inputs: "Tên đăng nhập / Email" and "Mật khẩu" (with an eye icon to toggle visibility).
- Options: "Ghi nhớ đăng nhập" checkbox and "Quên mật khẩu?" link.
- Primary action: Prominent blue "Đăng nhập" button.

### 7.2 User (Reader) Dashboard
- Left sidebar navigation: Trang chủ, Khám phá sách, Sách đang mượn, Lịch sử mượn, Danh sách yêu thích, Thông báo.
- Top search bar: "Tìm tên sách, tác giả, ISBN...".
- Main workspace: Personalized greeting, promotional banner, and three statistics cards ("Sách đang mượn: 03", "Sắp đến hạn: 01", "Điểm tích lũy: 120").
- Recommendations section: Book cards with covers, titles, authors, available copies, and a "Chi tiết" button.

### 7.3 Librarian Workspace
- Operational menus in sidebar: Mượn sách, Trả sách, Quản lý phiếu mượn, etc.
- Top right action buttons: "+ Nhận trả" and "+ Tạo phiếu mượn".
- Statistics widgets: "Yêu cầu chờ duyệt", "Đang mượn", "Cần trả hôm nay", "Sách quá hạn".
- Core component: "Giao dịch cần xử lý" table tracking loan IDs, readers, books, dates, status, and action buttons ("Duyệt", "Chi tiết").

### 7.4 Admin Dashboard
- System management sidebar and "+ Thêm đầu sách" action button.
- High-level metric cards: "Tổng đầu sách", "Độc giả đang hoạt động", "Sách đang được mượn", and "Sách quá hạn" with percentage trends.
- Visualizations: 7-day borrowing/returning activity line chart and book category donut chart.
- "Giao dịch gần đây" table logging recent system activities.