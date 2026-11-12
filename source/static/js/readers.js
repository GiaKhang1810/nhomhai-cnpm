async function readersRequest(url, options = {}) {
	const headers = new Headers(options.headers || {});
	headers.set('Accept', 'application/json');
	if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

	const response = await fetch(url, {
		...options,
		headers,
		cache: 'no-store',
		credentials: 'same-origin',
	});
	const contentType = response.headers.get('content-type') || '';
	const data = contentType.includes('application/json') ? await response.json().catch(() => null) : null;
	if (!data) {
		throw new Error(response.ok
			? 'Máy chủ không trả về JSON hợp lệ. Hãy tải lại trang và thử lại.'
			: `Yêu cầu thất bại (HTTP ${response.status}). Có thể phiên đăng nhập đã hết hạn.`);
	}
	if (!response.ok || data.success === false) {
		throw new Error(data.message || `Yêu cầu thất bại (HTTP ${response.status}).`);
	}
	return data;
}

const readerRows = document.getElementById('readerRows');
const readerMessage = document.getElementById('readerMessage');
const readerForm = document.getElementById('readerForm');
let readerLoadSequence = 0;

function setReaderMessage(message, isError = false) {
	readerMessage.textContent = message || '';
	readerMessage.className = `text-sm mt-2 ${isError ? 'text-red-600' : 'text-emerald-700'}`;
}

async function loadReaders() {
	const sequence = ++readerLoadSequence;
	const keyword = document.getElementById('readerSearch').value.trim();
	readerRows.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Đang tải danh sách độc giả...</td></tr>';
	try {
		const result = await readersRequest(`/api/readers/?q=${encodeURIComponent(keyword)}&_=${Date.now()}`);
		if (!Array.isArray(result.data)) throw new Error('Dữ liệu danh sách độc giả không đúng định dạng.');
		if (sequence !== readerLoadSequence) return result.data;

		readerRows.replaceChildren();
		if (result.data.length === 0) {
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 6;
			cell.className = 'py-6 text-center text-slate-400';
			cell.textContent = 'Chưa có độc giả phù hợp.';
			row.append(cell);
			readerRows.append(row);
			return result.data;
		}

		for (const item of result.data) {
			const row = document.createElement('tr');
			row.className = 'border-b last:border-0';
			for (const value of [item.reader_id, item.full_name, item.identity_number, item.card_expiry_date || '']) {
				const cell = document.createElement('td');
				cell.className = 'py-3 pr-3';
				cell.textContent = value ?? '';
				row.append(cell);
			}
			const status = document.createElement('td');
			status.className = 'py-3';
			status.textContent = item.account_status || 'UNKNOWN';
			row.append(status);

			const actions = document.createElement('td');
			actions.className = 'py-3 whitespace-nowrap';
			const edit = document.createElement('button');
			edit.type = 'button';
			edit.textContent = 'Sửa';
			edit.className = 'text-blue-600 mr-3';
			edit.addEventListener('click', () => editReader(item));

			const active = String(item.account_status).toUpperCase() === 'ACTIVE';
			const statusAction = document.createElement('button');
			statusAction.type = 'button';
			statusAction.textContent = active ? 'Khóa' : 'Mở khóa';
			statusAction.className = active ? 'text-amber-700 mr-3' : 'text-emerald-700 mr-3';
			statusAction.addEventListener('click', () => active ? deactivateReader(item.reader_id) : activateReader(item.reader_id));

			const remove = document.createElement('button');
			remove.type = 'button';
			remove.textContent = 'Xóa';
			remove.className = 'text-red-600';
			remove.addEventListener('click', () => deleteReader(item.reader_id));
			actions.append(edit, statusAction, remove);
			row.append(actions);
			readerRows.append(row);
		}
		return result.data;
	} catch (error) {
		if (sequence === readerLoadSequence) {
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 6;
			cell.className = 'py-4 text-center text-red-600';
			cell.textContent = error.message;
			row.append(cell);
			readerRows.replaceChildren(row);
		}
		throw error;
	}
}

async function editReader(reader) {
	const full_name = prompt('Họ tên', reader.full_name); if (full_name === null) return;
	const dob = prompt('Ngày sinh (YYYY-MM-DD)', reader.dob || ''); if (dob === null) return;
	const gender = prompt('Giới tính (MALE, FEMALE, OTHER)', reader.gender || ''); if (gender === null) return;
	const identity_number = prompt('Số giấy tờ', reader.identity_number); if (identity_number === null) return;
	const phone = prompt('Số điện thoại', reader.phone || ''); if (phone === null) return;
	const card_expiry_date = prompt('Ngày hết hạn (YYYY-MM-DD)', reader.card_expiry_date || ''); if (card_expiry_date === null) return;
	try {
		const payload = { full_name, dob, gender, identity_number, phone, card_expiry_date };
		const result = await readersRequest(`/api/readers/${encodeURIComponent(reader.reader_id)}?_=${Date.now()}`, {
			method: 'PUT', body: JSON.stringify(payload),
		});
		setReaderMessage(result.message || 'Cập nhật độc giả thành công.');
		await loadReaders();
	} catch (error) { setReaderMessage(error.message, true); }
}

async function changeReaderStatus(id, activate) {
	const action = activate ? 'Mở khóa' : 'Khóa';
	if (!confirm(`${action} thẻ độc giả ${id}?`)) return;
	try {
		const result = await readersRequest(`/api/readers/${encodeURIComponent(id)}/${activate ? 'activate' : 'deactivate'}?_=${Date.now()}`, { method: 'PATCH' });
		setReaderMessage(result.message || `${action} thẻ thành công.`);
		await loadReaders();
	} catch (error) { setReaderMessage(error.message, true); }
}

function deactivateReader(id) { return changeReaderStatus(id, false); }
function activateReader(id) { return changeReaderStatus(id, true); }

async function deleteReader(id) {
	if (!confirm(`Xóa vĩnh viễn hồ sơ độc giả ${id}? Nếu đã có lịch sử mượn/trả, hệ thống sẽ từ chối để bảo toàn dữ liệu.`)) return;
	try {
		const result = await readersRequest(`/api/readers/${encodeURIComponent(id)}?_=${Date.now()}`, { method: 'DELETE' });
		setReaderMessage(result.message || 'Đã xóa độc giả.');
		await loadReaders();
	} catch (error) { setReaderMessage(error.message, true); }
}

readerForm.addEventListener('submit', async event => {
	event.preventDefault();
	const form = event.currentTarget;
	const submitButton = form.querySelector('button[type="submit"], button:not([type])');
	const originalButtonText = submitButton?.textContent || 'Tạo độc giả';
	const payload = Object.fromEntries(new FormData(form).entries());
	setReaderMessage('Đang tạo hồ sơ độc giả...');
	if (submitButton) { submitButton.disabled = true; submitButton.textContent = 'Đang tạo...'; }

	try {
		const response = await readersRequest(`/api/readers/?_=${Date.now()}`, {
			method: 'POST', body: JSON.stringify(payload),
		});
		document.getElementById('readerSearch').value = '';
		try {
			const readers = await loadReaders();
			const created = readers.some(item => item.identity_number === String(payload.identity_number).trim());
			if (created) {
				form.reset();
				setReaderMessage(response.message || 'Tạo độc giả thành công.');
			} else {
				setReaderMessage('Máy chủ đã nhận yêu cầu tạo độc giả nhưng danh sách chưa hiển thị bản ghi mới. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.', true);
			}
		} catch (refreshError) {
			setReaderMessage(`Máy chủ đã tạo độc giả, nhưng không tải được danh sách mới: ${refreshError.message}. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.`, true);
		}
	} catch (error) {
		setReaderMessage(error.message, true);
	} finally {
		if (submitButton) { submitButton.disabled = false; submitButton.textContent = originalButtonText; }
	}
});

document.getElementById('searchReaders').addEventListener('click', () => loadReaders().catch(error => setReaderMessage(error.message, true)));
document.getElementById('readerSearch').addEventListener('keydown', event => {
	if (event.key === 'Enter') { event.preventDefault(); loadReaders().catch(error => setReaderMessage(error.message, true)); }
});
document.getElementById('reloadReaders')?.addEventListener('click', () => loadReaders().catch(error => setReaderMessage(error.message, true)));
loadReaders().catch(() => { });
