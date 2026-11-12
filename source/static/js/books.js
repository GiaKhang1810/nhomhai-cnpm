const booksApi = '/api/books/';
const bookRows = document.getElementById('bookRows');
const bookMessage = document.getElementById('bookMessage');
const bookListMessage = document.getElementById('bookListMessage');
const bookForm = document.getElementById('bookForm');
let bookLoadSequence = 0;

async function requestJson(url, options = {}) {
	const headers = new Headers(options.headers || {});
	headers.set('Accept', 'application/json');
	if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
	const response = await fetch(url, { ...options, headers, cache: 'no-store', credentials: 'same-origin' });
	const contentType = response.headers.get('content-type') || '';
	const data = contentType.includes('application/json') ? await response.json().catch(() => null) : null;
	if (!data) {
		throw new Error(response.ok
			? 'Máy chủ không trả về JSON hợp lệ. Hãy tải lại trang và thử lại.'
			: `Yêu cầu thất bại (HTTP ${response.status}). Có thể phiên đăng nhập đã hết hạn.`);
	}
	if (!response.ok || data.success === false) throw new Error(data.message || `Yêu cầu thất bại (HTTP ${response.status}).`);
	return data;
}

function setBookMessage(message, isError = false) {
	bookMessage.textContent = message || '';
	bookMessage.className = `text-sm mt-2 ${isError ? 'text-red-600' : 'text-emerald-700'}`;
}

function setBookListMessage(message, isError = false) {
	bookListMessage.textContent = message || '';
	bookListMessage.className = `text-sm mt-3 ${isError ? 'text-red-600' : 'text-slate-500'}`;
}

async function loadBooks() {
	const sequence = ++bookLoadSequence;
	const keyword = document.getElementById('bookSearch').value.trim();
	bookRows.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-400">Đang tải danh mục...</td></tr>';
	try {
		const result = await requestJson(`${booksApi}?q=${encodeURIComponent(keyword)}&include_inactive=true&_=${Date.now()}`);
		if (!Array.isArray(result.data)) throw new Error('Dữ liệu danh mục sách không đúng định dạng.');
		if (sequence !== bookLoadSequence) return result.data;

		bookRows.replaceChildren();
		setBookListMessage(`${result.count ?? result.data.length} đầu sách`);
		if (!result.data.length) {
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 7;
			cell.className = 'py-6 text-center text-slate-400';
			cell.textContent = 'Không tìm thấy đầu sách.';
			row.append(cell);
			bookRows.append(row);
			return result.data;
		}

		for (const book of result.data) {
			const row = document.createElement('tr');
			row.className = 'border-b last:border-0';
			const values = [book.book_code, book.title, book.author, `${book.available_quantity}/${book.total_quantity}`, `${Number(book.listed_value).toLocaleString('vi-VN')} đ`];
			for (const value of values) {
				const cell = document.createElement('td');
				cell.className = 'py-3 pr-3';
				cell.textContent = value ?? '';
				row.append(cell);
			}
			const statusCell = document.createElement('td');
			statusCell.className = 'py-3 pr-3';
			statusCell.textContent = book.is_active ? 'Đang kinh doanh' : 'Đã ngừng';
			row.append(statusCell);

			const action = document.createElement('td');
			action.className = 'py-3 whitespace-nowrap';
			const edit = document.createElement('button');
			edit.type = 'button'; edit.textContent = 'Sửa'; edit.className = 'text-blue-600 mr-3';
			edit.addEventListener('click', () => editBook(book));

			const statusAction = document.createElement('button');
			statusAction.type = 'button';
			statusAction.textContent = book.is_active ? 'Ngừng' : 'Mở lại';
			statusAction.className = book.is_active ? 'text-amber-700 mr-3' : 'text-emerald-700 mr-3';
			statusAction.addEventListener('click', () => changeBookStatus(book.book_code, !book.is_active));

			const remove = document.createElement('button');
			remove.type = 'button'; remove.textContent = 'Xóa'; remove.className = 'text-red-600';
			remove.addEventListener('click', () => deleteBook(book.book_code));
			action.append(edit, statusAction, remove);
			row.append(action);
			bookRows.append(row);
		}
		return result.data;
	} catch (error) {
		if (sequence === bookLoadSequence) {
			setBookListMessage(error.message, true);
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 7; cell.className = 'py-6 text-center text-red-600'; cell.textContent = error.message;
			row.append(cell); bookRows.replaceChildren(row);
		}
		throw error;
	}
}

async function editBook(book) {
	const title = prompt('Tên sách', book.title); if (title === null) return;
	const author = prompt('Tác giả', book.author); if (author === null) return;
	const publisher = prompt('Nhà xuất bản', book.publisher || ''); if (publisher === null) return;
	const year = prompt('Năm xuất bản', book.publication_year ?? ''); if (year === null) return;
	const category = prompt('Thể loại', book.category || ''); if (category === null) return;
	const quantity = prompt('Tổng số bản sao', String(book.total_quantity)); if (quantity === null) return;
	const listedValue = prompt('Giá trị bồi thường (VND)', String(book.listed_value)); if (listedValue === null) return;
	try {
		const payload = { title, author, publisher, publication_year: year, category, total_quantity: quantity, listed_value: listedValue };
		const result = await requestJson(`${booksApi}${encodeURIComponent(book.book_code)}?_=${Date.now()}`, { method: 'PUT', body: JSON.stringify(payload) });
		setBookListMessage(result.message || 'Cập nhật đầu sách thành công.');
		await loadBooks();
	} catch (error) { setBookListMessage(error.message, true); }
}

async function changeBookStatus(code, activate) {
	const action = activate ? 'Mở lại' : 'Ngừng kinh doanh';
	if (!confirm(`${action} đầu sách ${code}?`)) return;
	try {
		const result = await requestJson(`${booksApi}${encodeURIComponent(code)}/${activate ? 'activate' : 'deactivate'}?_=${Date.now()}`, { method: 'PATCH' });
		setBookListMessage(result.message || `${action} thành công.`);
		await loadBooks();
	} catch (error) { setBookListMessage(error.message, true); }
}

async function deleteBook(code) {
	if (!confirm(`Xóa vĩnh viễn đầu sách ${code} và các bản sao? Nếu đã phát sinh lịch sử mượn/trả, hệ thống sẽ từ chối để bảo toàn dữ liệu.`)) return;
	try {
		const result = await requestJson(`${booksApi}${encodeURIComponent(code)}?_=${Date.now()}`, { method: 'DELETE' });
		setBookListMessage(result.message || 'Đã xóa đầu sách.');
		await loadBooks();
	} catch (error) { setBookListMessage(error.message, true); }
}

bookForm.addEventListener('submit', async event => {
	event.preventDefault();
	const form = event.currentTarget;
	const submitButton = form.querySelector('button[type="submit"], button:not([type])');
	const originalButtonText = submitButton?.textContent || 'Thêm sách';
	const payload = Object.fromEntries(new FormData(form).entries());
	setBookMessage('Đang thêm đầu sách...');
	if (submitButton) { submitButton.disabled = true; submitButton.textContent = 'Đang thêm...'; }

	try {
		const response = await requestJson(`${booksApi}?_=${Date.now()}`, { method: 'POST', body: JSON.stringify(payload) });
		document.getElementById('bookSearch').value = '';
		try {
			const books = await loadBooks();
			const created = books.some(item => String(item.book_code).toUpperCase() === String(payload.book_code).trim().toUpperCase());
			if (created) {
				form.reset();
				setBookMessage(response.message || 'Thêm đầu sách thành công.');
			} else {
				setBookMessage('Máy chủ đã nhận yêu cầu thêm sách nhưng danh mục chưa hiển thị bản ghi mới. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.', true);
			}
		} catch (refreshError) {
			setBookMessage(`Máy chủ đã lưu đầu sách, nhưng không tải được danh mục mới: ${refreshError.message}. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.`, true);
		}
	} catch (error) {
		setBookMessage(error.message, true);
	} finally {
		if (submitButton) { submitButton.disabled = false; submitButton.textContent = originalButtonText; }
	}
});

document.getElementById('searchBooks').addEventListener('click', () => loadBooks().catch(error => setBookListMessage(error.message, true)));
document.getElementById('bookSearch').addEventListener('keydown', event => {
	if (event.key === 'Enter') { event.preventDefault(); loadBooks().catch(error => setBookListMessage(error.message, true)); }
});
document.getElementById('reloadBooks')?.addEventListener('click', () => loadBooks().catch(error => setBookListMessage(error.message, true)));
loadBooks().catch(() => { });
