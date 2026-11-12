async function accountsRequest(url, options = {}) {
	const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options }); const result = await response.json().catch(() => ({}));
	if (!response.ok || !result.success) throw new Error(result.message || 'Yêu cầu không thành công.'); return result;
}
async function loadStaff() {
	const tbody = document.getElementById('staffRows'); tbody.replaceChildren();
	try {
		const result = await accountsRequest('/api/accounts/');
		for (const staff of result.data) {
			const row = document.createElement('tr'); row.className = 'border-b last:border-0';
			const fields = [];
			for (const [value, placeholder] of [[staff.full_name || '', 'Họ tên'], [staff.username, 'Tên đăng nhập'], [staff.email, 'Email']]) {
				const cell = document.createElement('td'); cell.className = 'py-3 pr-3 min-w-40';
				const input = document.createElement('input'); input.value = value || ''; input.placeholder = placeholder;
				input.className = 'w-full border rounded-lg px-2 py-1'; input.disabled = staff.account_status !== 'ACTIVE';
				cell.append(input); row.append(cell); fields.push(input);
			}
			const roleCell = document.createElement('td'); const select = document.createElement('select'); select.className = 'border rounded p-1';
			for (const role of ['LIBRARIAN', 'ADMIN']) { const option = document.createElement('option'); option.value = role; option.textContent = role; option.selected = role === staff.role; select.append(option); }
			select.disabled = staff.account_status !== 'ACTIVE'; select.onchange = async () => { try { await accountsRequest(`/api/accounts/${staff.user_id}`, { method: 'PUT', body: JSON.stringify({ role: select.value }) }); await loadStaff(); } catch (error) { alert(error.message); await loadStaff(); } }; roleCell.append(select); row.append(roleCell);
			const status = document.createElement('td'); status.className = 'py-3'; status.textContent = staff.account_status; row.append(status);
			const action = document.createElement('td'); action.className = 'py-3 whitespace-nowrap';
			const save = document.createElement('button'); save.textContent = 'Lưu'; save.className = 'text-blue-600 mr-3'; save.disabled = staff.account_status !== 'ACTIVE';
			save.onclick = async () => {
				const payload = { username: fields[1].value.trim(), email: fields[2].value.trim() };
				if (staff.role === 'LIBRARIAN') payload.full_name = fields[0].value.trim();
				try { await accountsRequest(`/api/accounts/${staff.user_id}`, { method: 'PUT', body: JSON.stringify(payload) }); await loadStaff(); }
				catch (error) { alert(error.message); }
			};
			const deactivate = document.createElement('button'); deactivate.textContent = 'Khóa'; deactivate.className = 'text-red-600'; deactivate.disabled = staff.account_status !== 'ACTIVE';
			deactivate.onclick = async () => { if (!confirm(`Khóa tài khoản ${staff.username}?`)) return; try { await accountsRequest(`/api/accounts/${staff.user_id}/deactivate`, { method: 'PATCH' }); await loadStaff(); } catch (error) { alert(error.message); } };
			action.append(save, deactivate); row.append(action); tbody.append(row);
		}
		if (!result.data.length) {
			const tr = document.createElement('tr'); const td = document.createElement('td');
			td.colSpan = 6; td.className = 'py-6 text-center text-slate-400'; td.textContent = 'Chưa có tài khoản nhân viên.';
			tr.append(td); tbody.append(tr);
		}
	} catch (error) {
		const tr = document.createElement('tr'); const td = document.createElement('td');
		td.colSpan = 6; td.className = 'py-4 text-red-600'; td.textContent = error.message;
		tr.append(td); tbody.replaceChildren(tr);
	}
}
document.getElementById('staffForm').addEventListener('submit', async event => {
	event.preventDefault(); const message = document.getElementById('staffMessage');
	try { const result = await accountsRequest('/api/accounts/', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget).entries())) }); message.textContent = result.message; event.currentTarget.reset(); await loadStaff(); }
	catch (error) { message.textContent = error.message; }
});
document.getElementById('reloadStaff').addEventListener('click', loadStaff); loadStaff();
