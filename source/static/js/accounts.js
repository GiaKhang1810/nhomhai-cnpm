async function accountsRequest(url, options = {}) {
	const headers = new Headers(options.headers || {});
	headers.set('Accept', 'application/json');
	if (options.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}

	const response = await fetch(url, {
		...options,
		headers,
		cache: 'no-store',
		credentials: 'same-origin',
	});
	const contentType = response.headers.get('content-type') || '';
	const result = contentType.includes('application/json')
		? await response.json().catch(() => null)
		: null;

	if (!result) {
		throw new Error(response.ok
			? 'Máy chủ không trả về dữ liệu JSON hợp lệ. Hãy tải lại trang và thử lại.'
			: `Yêu cầu thất bại (HTTP ${response.status}). Vui lòng đăng nhập lại nếu phiên làm việc đã hết hạn.`);
	}
	if (!response.ok || result.success === false) {
		throw new Error(result.message || `Yêu cầu thất bại (HTTP ${response.status}).`);
	}
	return result;
}

const staffRows = document.getElementById('staffRows');
const staffMessage = document.getElementById('staffMessage');
const staffForm = document.getElementById('staffForm');
let staffLoadSequence = 0;

function setStaffMessage(message, isError = false) {
	staffMessage.textContent = message || '';
	staffMessage.className = `text-sm mt-2 ${isError ? 'text-red-600' : 'text-emerald-700'}`;
}

function createStaffInput(value, placeholder, disabled = false) {
	const input = document.createElement('input');
	input.value = value ?? '';
	input.placeholder = placeholder;
	input.disabled = disabled;
	input.autocomplete = 'off';
	input.className = 'w-full min-w-36 border rounded-lg px-2 py-1 disabled:bg-slate-100 disabled:text-slate-400';
	return input;
}

async function loadStaff() {
	const sequence = ++staffLoadSequence;
	staffRows.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Đang tải danh sách nhân viên...</td></tr>';

	try {
		const result = await accountsRequest(`/api/accounts/?_=${Date.now()}`);
		if (!Array.isArray(result.data)) {
			throw new Error('Dữ liệu danh sách nhân viên không đúng định dạng.');
		}
		if (sequence !== staffLoadSequence) return result.data;

		staffRows.replaceChildren();
		for (const staff of result.data) {
			const row = document.createElement('tr');
			row.className = 'border-b last:border-0';
			const isActive = String(staff.account_status).toUpperCase() === 'ACTIVE';
			const isLibrarianProfile = Boolean(staff.staff_id) || String(staff.role).toUpperCase() === 'LIBRARIAN';

			const nameCell = document.createElement('td');
			nameCell.className = 'py-3 pr-3 min-w-40';
			const nameInput = createStaffInput(staff.full_name, 'Họ tên', !isActive || !isLibrarianProfile);
			nameInput.setAttribute('aria-label', `Họ tên ${staff.username}`);
			nameCell.append(nameInput);
			row.append(nameCell);

			const usernameCell = document.createElement('td');
			usernameCell.className = 'py-3 pr-3 min-w-40';
			const usernameInput = createStaffInput(staff.username, 'Tên đăng nhập', !isActive);
			usernameInput.setAttribute('aria-label', `Tên đăng nhập ${staff.username}`);
			usernameCell.append(usernameInput);
			row.append(usernameCell);

			const emailCell = document.createElement('td');
			emailCell.className = 'py-3 pr-3 min-w-44';
			const emailInput = createStaffInput(staff.email, 'Email', !isActive);
			emailInput.type = 'email';
			emailInput.setAttribute('aria-label', `Email ${staff.username}`);
			emailCell.append(emailInput);
			row.append(emailCell);

			const roleCell = document.createElement('td');
			roleCell.className = 'py-3 pr-2';
			const roleSelect = document.createElement('select');
			roleSelect.className = 'border rounded p-1';
			roleSelect.disabled = !isActive;
			for (const role of ['LIBRARIAN', 'ADMIN']) {
				const option = document.createElement('option');
				option.value = role;
				option.textContent = role;
				option.selected = role === String(staff.role).toUpperCase();
				roleSelect.append(option);
			}
			roleSelect.addEventListener('change', async () => {
				const previousRole = String(staff.role).toUpperCase();
				const nextRole = roleSelect.value;
				const payload = { role: nextRole };
				if (nextRole === 'LIBRARIAN' && !staff.staff_id) {
					const fullName = prompt('Nhập họ tên thủ thư:', '');
					if (fullName === null || !fullName.trim()) {
						roleSelect.value = previousRole;
						return;
					}
					payload.full_name = fullName.trim();
				}
				roleSelect.disabled = true;
				try {
					const response = await accountsRequest(`/api/accounts/${staff.user_id}?_=${Date.now()}`, {
						method: 'PUT', body: JSON.stringify(payload),
					});
					setStaffMessage(response.message || 'Đã cập nhật vai trò.');
					await loadStaff();
				} catch (error) {
					setStaffMessage(error.message, true);
					await loadStaff();
				}
			});
			roleCell.append(roleSelect);
			row.append(roleCell);

			const statusCell = document.createElement('td');
			statusCell.className = 'py-3 whitespace-nowrap';
			statusCell.textContent = staff.account_status || 'UNKNOWN';
			row.append(statusCell);

			const actionCell = document.createElement('td');
			actionCell.className = 'py-3 whitespace-nowrap';

			const save = document.createElement('button');
			save.type = 'button';
			save.textContent = 'Lưu';
			save.className = 'text-blue-600 hover:text-blue-800 mr-3';
			save.disabled = !isActive;
			save.addEventListener('click', async () => {
				const payload = {
					username: usernameInput.value.trim(),
					email: emailInput.value.trim(),
				};
				if (isLibrarianProfile) {
					payload.full_name = nameInput.value.trim();
				}
				if (!payload.username || !payload.email) {
					setStaffMessage('Tên đăng nhập và email không được để trống.', true);
					return;
				}
				if (isLibrarianProfile && !payload.full_name) {
					setStaffMessage('Họ tên nhân viên không được để trống.', true);
					nameInput.focus();
					return;
				}

				save.disabled = true;
				save.textContent = 'Đang lưu...';
				try {
					const response = await accountsRequest(`/api/accounts/${staff.user_id}?_=${Date.now()}`, {
						method: 'PUT', body: JSON.stringify(payload),
					});
					setStaffMessage(response.message || 'Cập nhật tài khoản thành công.');
					await loadStaff();
				} catch (error) {
					setStaffMessage(error.message, true);
					save.disabled = false;
					save.textContent = 'Lưu';
				}
			});

			const statusAction = document.createElement('button');
			statusAction.type = 'button';
			statusAction.textContent = isActive ? 'Khóa' : 'Mở khóa';
			statusAction.className = `${isActive ? 'text-amber-700' : 'text-emerald-700'} mr-3`;
			statusAction.addEventListener('click', async () => {
				const activate = !isActive;
				const verb = activate ? 'Mở khóa' : 'Khóa';
				if (!confirm(`${verb} tài khoản ${staff.username}?`)) return;
				try {
					const response = await accountsRequest(`/api/accounts/${staff.user_id}/${activate ? 'activate' : 'deactivate'}?_=${Date.now()}`, { method: 'PATCH' });
					setStaffMessage(response.message || `${verb} tài khoản thành công.`);
					await loadStaff();
				} catch (error) {
					setStaffMessage(error.message, true);
				}
			});

			const remove = document.createElement('button');
			remove.type = 'button';
			remove.textContent = 'Xóa';
			remove.className = 'text-red-600 hover:text-red-800';
			remove.addEventListener('click', async () => {
				if (!confirm(`Xóa vĩnh viễn tài khoản ${staff.username}? Thao tác này không thể hoàn tác.`)) return;
				try {
					const response = await accountsRequest(`/api/accounts/${staff.user_id}?_=${Date.now()}`, { method: 'DELETE' });
					setStaffMessage(response.message || 'Đã xóa tài khoản.');
					await loadStaff();
				} catch (error) {
					setStaffMessage(error.message, true);
				}
			});

			actionCell.append(save, statusAction, remove);
			row.append(actionCell);
			staffRows.append(row);
		}

		if (result.data.length === 0) {
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 6;
			cell.className = 'py-6 text-center text-slate-400';
			cell.textContent = 'Chưa có tài khoản nhân viên.';
			row.append(cell);
			staffRows.append(row);
		}
		return result.data;
	} catch (error) {
		if (sequence === staffLoadSequence) {
			const row = document.createElement('tr');
			const cell = document.createElement('td');
			cell.colSpan = 6;
			cell.className = 'py-4 text-red-600';
			cell.textContent = error.message;
			row.append(cell);
			staffRows.replaceChildren(row);
		}
		throw error;
	}
}

staffForm.addEventListener('submit', async event => {
	event.preventDefault();
	const form = event.currentTarget;
	const submitButton = form.querySelector('button[type="submit"], button:not([type])');
	const originalButtonText = submitButton?.textContent || 'Tạo tài khoản';
	const payload = Object.fromEntries(new FormData(form).entries());
	setStaffMessage('Đang tạo tài khoản...');
	if (submitButton) { submitButton.disabled = true; submitButton.textContent = 'Đang tạo...'; }

	try {
		const response = await accountsRequest(`/api/accounts/?_=${Date.now()}`, {
			method: 'POST', body: JSON.stringify(payload),
		});
		try {
			const staff = await loadStaff();
			const created = staff.some(item => item.username === payload.username || item.email === payload.email);
			if (created) {
				form.reset();
				setStaffMessage(response.message || 'Tạo tài khoản thành công.');
			} else {
				setStaffMessage('Máy chủ đã nhận yêu cầu tạo tài khoản nhưng danh sách chưa hiển thị bản ghi mới. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.', true);
			}
		} catch (refreshError) {
			setStaffMessage(`Máy chủ đã tạo tài khoản, nhưng không tải được danh sách mới: ${refreshError.message}. Hãy bấm Tải lại; không gửi lại biểu mẫu lúc này.`, true);
		}
	} catch (error) {
		setStaffMessage(error.message, true);
	} finally {
		if (submitButton) { submitButton.disabled = false; submitButton.textContent = originalButtonText; }
	}
});

document.getElementById('reloadStaff').addEventListener('click', () => loadStaff().catch(error => setStaffMessage(error.message, true)));
loadStaff().catch(() => { });
