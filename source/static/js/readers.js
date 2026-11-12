async function readersRequest(url, options = {}) {
	const response = await fetch(url, { credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, ...options });
	const data = await response.json().catch(() => ({}));
	if (!response.ok || data.success === false) throw new Error(data.message || 'Yêu cầu không thành công.');
	return data;
}
const readerRows = document.getElementById('readerRows');
async function loadReaders() {
	const q = document.getElementById('readerSearch').value.trim(); if (!q) { readerRows.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Nhập từ khóa để tìm độc giả.</td></tr>'; return; }
	try {
		const result = await readersRequest(`/api/readers/search?q=${encodeURIComponent(q)}`); readerRows.replaceChildren();
		for (const item of result.data) {
			const tr = document.createElement('tr'); tr.className = 'border-b last:border-0';
			for (const value of [item.reader_id, item.full_name, item.identity_number, item.card_expiry_date || '']) { const td = document.createElement('td'); td.className = 'py-3 pr-3'; td.textContent = value; tr.append(td); }
			const status = document.createElement('td'); status.className = 'py-3'; status.textContent = item.account_status; tr.append(status);
			const actions = document.createElement('td'); const edit = document.createElement('button'); edit.textContent = 'Sửa'; edit.className = 'text-blue-600 mr-3'; edit.onclick = () => editReader(item);
			const disable = document.createElement('button'); disable.textContent = 'Khóa'; disable.className = 'text-red-600'; disable.disabled = item.account_status !== 'ACTIVE'; disable.onclick = () => deactivateReader(item.reader_id);
			actions.append(edit, disable); tr.append(actions); readerRows.append(tr);
		}
		if (!result.data.length) readerRows.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Không tìm thấy độc giả.</td></tr>';
	} catch (error) {
		const tr = document.createElement('tr'); const td = document.createElement('td');
		td.colSpan = 6; td.className = 'py-4 text-red-600'; td.textContent = error.message;
		tr.append(td); readerRows.replaceChildren(tr);
	}
}
async function editReader(reader) {
	const full_name = prompt('Họ tên', reader.full_name); if (full_name === null) return;
	const dob = prompt('Ngày sinh (YYYY-MM-DD)', reader.dob || ''); if (dob === null) return;
	const gender = prompt('Giới tính (MALE, FEMALE, OTHER)', reader.gender || ''); if (gender === null) return;
	const identity_number = prompt('Số giấy tờ', reader.identity_number); if (identity_number === null) return;
	const phone = prompt('Số điện thoại', reader.phone || ''); if (phone === null) return;
	const card_expiry_date = prompt('Ngày hết hạn (YYYY-MM-DD)', reader.card_expiry_date || ''); if (card_expiry_date === null) return;
	try { const payload = { full_name, dob, gender, identity_number, phone, card_expiry_date }; const result = await readersRequest(`/api/readers/${encodeURIComponent(reader.reader_id)}`, { method: 'PUT', body: JSON.stringify(payload) }); document.getElementById('readerMessage').textContent = result.message; await loadReaders(); }
	catch (error) { document.getElementById('readerMessage').textContent = error.message; }
}
async function deactivateReader(id) {
	if (!confirm(`Khóa thẻ độc giả ${id}?`)) return;
	try { const result = await readersRequest(`/api/readers/${encodeURIComponent(id)}/deactivate`, { method: 'PATCH' }); document.getElementById('readerMessage').textContent = result.message; await loadReaders(); }
	catch (error) { document.getElementById('readerMessage').textContent = error.message; }
}
document.getElementById('readerForm').addEventListener('submit', async event => {
	event.preventDefault(); const message = document.getElementById('readerMessage'); message.textContent = 'Đang lưu...';
	try { const result = await readersRequest('/api/readers/', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget).entries())) }); message.textContent = result.message; event.currentTarget.reset(); }
	catch (error) { message.textContent = error.message; }
});
document.getElementById('searchReaders').addEventListener('click', loadReaders);
document.getElementById('readerSearch').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); loadReaders(); } });
