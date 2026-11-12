const selectedCopies = new Map();
const bookResults = document.getElementById('borrowBookResults');
const copyResults = document.getElementById('availableCopyResults');
const selectedList = document.getElementById('selectedCopyList');
const borrowMessage = document.getElementById('borrowMessage');

async function borrowApi(url) {
	const response = await fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
	const result = await response.json().catch(() => ({}));
	if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tải dữ liệu.');
	return result;
}

function renderSelectedCopies() {
	selectedList.replaceChildren();
	for (const [copyId, title] of selectedCopies) {
		const item = document.createElement('li'); item.className = 'flex items-center justify-between gap-3 border rounded-lg px-3 py-2 text-sm';
		const label = document.createElement('span'); label.textContent = `${title} · ${copyId}`;
		const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Bỏ chọn'; remove.className = 'text-red-600 shrink-0';
		remove.addEventListener('click', () => { selectedCopies.delete(copyId); renderSelectedCopies(); });
		item.append(label, remove); selectedList.append(item);
	}
	document.getElementById('selectedCopyCount').textContent = `${selectedCopies.size}/5 bản sao đã chọn`;
}

async function loadAvailableCopies(book) {
	copyResults.replaceChildren();
	try {
		const result = await borrowApi(`/api/books/${encodeURIComponent(book.book_code)}/copies`);
		const heading = document.createElement('h3'); heading.className = 'font-semibold text-sm mb-2';
		heading.textContent = `${book.title} — Các bản sao còn khả dụng`;
		copyResults.append(heading);
		if (!result.data.length) {
			const empty = document.createElement('p'); empty.className = 'text-sm text-slate-500'; empty.textContent = 'Hiện không có bản sao khả dụng.';
			copyResults.append(empty); return;
		}
		for (const copy of result.data) {
			const label = document.createElement('label'); label.className = 'inline-flex items-center gap-2 border rounded-lg px-3 py-2 mr-2 mb-2 text-sm';
			const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.value = copy.copy_id;
			checkbox.checked = selectedCopies.has(copy.copy_id);
			checkbox.addEventListener('change', () => {
				if (checkbox.checked) {
					if (selectedCopies.size >= 5) {
						checkbox.checked = false;
						borrowMessage.textContent = 'Mỗi phiếu mượn chỉ được chọn tối đa 5 bản sao.';
						return;
					}
					selectedCopies.set(copy.copy_id, book.title);
				} else selectedCopies.delete(copy.copy_id);
				borrowMessage.textContent = '';
				renderSelectedCopies();
			});
			const text = document.createElement('span'); text.textContent = copy.copy_id;
			label.append(checkbox, text); copyResults.append(label);
		}
	} catch (error) { copyResults.textContent = error.message; }
}

async function searchBorrowBooks() {
	const keyword = document.getElementById('borrowBookSearch').value.trim();
	bookResults.replaceChildren(); copyResults.replaceChildren();
	if (!keyword) { borrowMessage.textContent = 'Nhập tên sách, tác giả hoặc mã sách để tìm.'; return; }
	try {
		const result = await borrowApi(`/api/books/?q=${encodeURIComponent(keyword)}`);
		if (!result.data.length) { bookResults.textContent = 'Không tìm thấy đầu sách phù hợp.'; return; }
		for (const book of result.data) {
			const row = document.createElement('div'); row.className = 'flex flex-wrap items-center justify-between gap-3 border rounded-xl p-3';
			const info = document.createElement('div');
			const title = document.createElement('p'); title.className = 'font-semibold text-sm'; title.textContent = book.title;
			const meta = document.createElement('p'); meta.className = 'text-xs text-slate-500 mt-1'; meta.textContent = `${book.book_code} · ${book.author} · Còn ${book.available_quantity}/${book.total_quantity} bản`;
			info.append(title, meta);
			const choose = document.createElement('button'); choose.type = 'button'; choose.textContent = 'Chọn bản sao'; choose.className = 'text-sm bg-blue-50 text-blue-700 rounded-lg px-3 py-2';
			choose.disabled = Number(book.available_quantity) <= 0;
			choose.addEventListener('click', () => loadAvailableCopies(book));
			row.append(info, choose); bookResults.append(row);
		}
		borrowMessage.textContent = '';
	} catch (error) { borrowMessage.textContent = error.message; }
}

document.getElementById('searchBorrowBooks').addEventListener('click', searchBorrowBooks);
document.getElementById('borrowBookSearch').addEventListener('keydown', event => {
	if (event.key === 'Enter') { event.preventDefault(); searchBorrowBooks(); }
});

document.getElementById('borrowForm').addEventListener('submit', async event => {
	event.preventDefault();
	const readerId = document.getElementById('readerId').value.trim();
	if (!readerId) { borrowMessage.textContent = 'Vui lòng nhập mã độc giả.'; return; }
	if (!selectedCopies.size) { borrowMessage.textContent = 'Hãy chọn ít nhất một bản sao sách.'; return; }
	borrowMessage.textContent = 'Đang xử lý giao dịch...';
	try {
		const response = await fetch('/borrowing/create', {
			method: 'POST', credentials: 'same-origin',
			headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
			body: JSON.stringify({ reader_id: readerId, copy_ids: [...selectedCopies.keys()] }),
		});
		const result = await response.json().catch(() => ({}));
		if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tạo phiếu mượn.');
		borrowMessage.className = 'text-sm mt-2 text-emerald-600';
		borrowMessage.textContent = result.message;
		selectedCopies.clear(); renderSelectedCopies();
		copyResults.replaceChildren(); bookResults.replaceChildren();
		document.getElementById('borrowBookSearch').value = '';
		event.currentTarget.reset();
	} catch (error) {
		borrowMessage.className = 'text-sm mt-2 text-red-600'; borrowMessage.textContent = error.message;
	}
});

renderSelectedCopies();
