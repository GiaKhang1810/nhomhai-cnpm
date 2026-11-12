const dialog = document.getElementById('bookDialog');
async function showBook(code) {
	try {
		const response = await fetch(`/api/books/${encodeURIComponent(code)}`); const result = await response.json();
		if (!response.ok || !result.success) throw new Error(result.message || 'Không tìm thấy sách.');
		const book = result.data; const target = document.getElementById('bookDetails'); target.replaceChildren();
		for (const [label, value] of [['Mã sách', book.book_code], ['Tên sách', book.title], ['Tác giả', book.author], ['Nhà xuất bản', book.publisher || '—'], ['Năm xuất bản', book.publication_year || '—'], ['Thể loại', book.category || '—'], ['Tổng số bản', book.total_quantity], ['Bản còn khả dụng', book.available_quantity]]) {
			const row = document.createElement('p'); const strong = document.createElement('strong'); strong.textContent = `${label}: `; row.append(strong, document.createTextNode(String(value))); target.append(row);
		}
		dialog.showModal();
	} catch (error) { document.getElementById('catalogueMessage').textContent = error.message; }
}
function bindDetails() { document.querySelectorAll('.detailBook').forEach(button => button.addEventListener('click', () => showBook(button.dataset.code))); }
async function requestBorrow(button) {
	const message = document.getElementById('catalogueMessage');
	const quantityText = window.prompt(`Số bản muốn đăng ký mượn cho "${button.dataset.title || 'đầu sách này'}" (1–5):`, '1');
	if (quantityText === null) return;
	const quantity = Number(quantityText);
	if (!Number.isInteger(quantity) || quantity < 1 || quantity > 5) { message.textContent = 'Số lượng phải là số nguyên từ 1 đến 5.'; return; }
	button.disabled = true;
	try {
		const response = await fetch('/profile/api/borrow-requests', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify({ book_code: button.dataset.code, quantity }), cache: 'no-store' });
		const result = await response.json().catch(() => ({}));
		if (!response.ok || !result.success) throw new Error(result.message || 'Không thể gửi yêu cầu mượn.');
		message.className = 'text-sm text-emerald-600 mt-4';
		message.textContent = `${result.message} Mã yêu cầu: ${result.request_id}`;
	} catch (error) {
		message.className = 'text-sm text-red-600 mt-4'; message.textContent = error.message;
	} finally { button.disabled = false; }
}
document.addEventListener('click', event => {
	const button = event.target.closest('.requestBorrow');
	if (button) requestBorrow(button);
});
bindDetails();
document.getElementById('closeBookDialog').addEventListener('click', () => dialog.close());
document.getElementById('catalogueSearch').addEventListener('submit', async event => {
	event.preventDefault(); const query = document.getElementById('keyword').value.trim(); const container = document.getElementById('catalogueResults');
	try {
		const response = await fetch(`/api/books/?q=${encodeURIComponent(query)}`); const result = await response.json(); if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tìm sách.');
		container.replaceChildren();
		for (const book of result.data) {
			const card = document.createElement('article'); card.className = 'border rounded-xl p-4 bg-white';
			const code = document.createElement('p'); code.className = 'text-xs text-blue-600 font-semibold'; code.textContent = book.book_code;
			const title = document.createElement('h2'); title.className = 'font-semibold mt-2'; title.textContent = book.title;
			const author = document.createElement('p'); author.className = 'text-sm text-slate-500'; author.textContent = book.author;
			const available = document.createElement('p'); available.className = 'text-sm mt-3'; available.textContent = `Còn ${book.available_quantity} bản`;
			const actions = document.createElement('div'); actions.className = 'flex flex-wrap items-center gap-3 mt-3';
			const detail = document.createElement('button'); detail.className = 'detailBook text-sm text-blue-600'; detail.textContent = 'Xem chi tiết'; detail.dataset.code = book.book_code; detail.addEventListener('click', () => showBook(book.book_code));
			const request = document.createElement('button'); request.type = 'button'; request.className = 'requestBorrow rounded-lg bg-blue-600 text-white px-3 py-2 text-xs disabled:opacity-40'; request.textContent = 'Đăng ký mượn'; request.dataset.code = book.book_code; request.dataset.title = book.title; request.disabled = Number(book.available_quantity) <= 0;
			actions.append(detail, request); card.append(code, title, author, available, actions); container.append(card);
		}
		if (!result.data.length) container.textContent = 'Không tìm thấy sách phù hợp.';
	} catch (error) { document.getElementById('catalogueMessage').textContent = error.message; }
});

const initialBookCode = new URLSearchParams(window.location.search).get('book_code');
if (initialBookCode) showBook(initialBookCode);
