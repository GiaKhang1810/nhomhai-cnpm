const booksApi = '/api/books/';
const bookRows = document.getElementById('bookRows');
const bookMessage = document.getElementById('bookMessage');
const bookListMessage = document.getElementById('bookListMessage');

async function requestJson(url, options = {}) {
	const response = await fetch(url, { credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
	const data = await response.json().catch(() => ({}));
	if (!response.ok || data.success === false) throw new Error(data.message || 'Yêu cầu không thành công.');
	return data;
}

async function loadBooks() {
	bookRows.replaceChildren();
	const keyword = document.getElementById('bookSearch').value.trim();
	try {
		const result = await requestJson(`${booksApi}?q=${encodeURIComponent(keyword)}`);
		bookListMessage.textContent = `${result.count} đầu sách`;
		if (!result.data.length) {
			bookRows.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Không tìm thấy đầu sách.</td></tr>';
			return;
		}
		for (const book of result.data) {
			const row = document.createElement('tr');
			row.className = 'border-b last:border-0';
			const values = [book.book_code, book.title, book.author, `${book.available_quantity}/${book.total_quantity}`, `${Number(book.listed_value).toLocaleString('vi-VN')} đ`];
			for (const value of values) { const cell = document.createElement('td'); cell.className = 'py-3 pr-3'; cell.textContent = value ?? ''; row.append(cell); }
			const action = document.createElement('td'); action.className = 'py-3 whitespace-nowrap';
			const edit = document.createElement('button'); edit.textContent = 'Sửa'; edit.className = 'text-blue-600 mr-3'; edit.addEventListener('click', () => editBook(book));
			const deactivate = document.createElement('button'); deactivate.textContent = 'Ngừng'; deactivate.className = 'text-red-600'; deactivate.addEventListener('click', () => deactivateBook(book.book_code));
			action.append(edit, deactivate); row.append(action); bookRows.append(row);
		}
	} catch (error) { bookListMessage.textContent = error.message; }
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
		const result = await requestJson(`${booksApi}${encodeURIComponent(book.book_code)}`, { method: 'PUT', body: JSON.stringify(payload) });
		bookListMessage.textContent = result.message; await loadBooks();
	} catch (error) { bookListMessage.textContent = error.message; }
}

async function deactivateBook(code) {
	if (!confirm(`Ngừng kinh doanh đầu sách ${code}?`)) return;
	try { const result = await requestJson(`${booksApi}${encodeURIComponent(code)}`, { method: 'DELETE' }); bookListMessage.textContent = result.message; await loadBooks(); }
	catch (error) { bookListMessage.textContent = error.message; }
}

document.getElementById('bookForm').addEventListener('submit', async event => {
	event.preventDefault(); bookMessage.textContent = 'Đang lưu...';
	const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
	try { const result = await requestJson(booksApi, { method: 'POST', body: JSON.stringify(payload) }); bookMessage.textContent = result.message; event.currentTarget.reset(); await loadBooks(); }
	catch (error) { bookMessage.textContent = error.message; }
});
document.getElementById('searchBooks').addEventListener('click', loadBooks);
document.getElementById('bookSearch').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); loadBooks(); } });
loadBooks();
