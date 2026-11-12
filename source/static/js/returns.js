let currentLoan = null;
const panel = document.getElementById('loanPanel');
const message = document.getElementById('returnMessage');
const resultsPanel = document.getElementById('loanResults');

async function loadLoanDetails(loanId) {
	const response = await fetch(`/borrowing/lookup/${encodeURIComponent(loanId)}`);
	const result = await response.json();
	if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tra cứu phiếu mượn.');
	currentLoan = result.data;
	document.getElementById('loanInfo').textContent = `Phiếu ${currentLoan.loan_id} · ${currentLoan.full_name} · Hạn trả ${new Date(currentLoan.due_date).toLocaleDateString('vi-VN')}`;
	const container = document.getElementById('returnItems'); container.replaceChildren();
	const pending = currentLoan.items.filter(item => !item.return_date);
	for (const item of pending) {
		const row = document.createElement('label'); row.className = 'flex flex-wrap items-center gap-3 border rounded-xl p-3';
		const check = document.createElement('input'); check.type = 'checkbox'; check.value = item.copy_id; check.className = 'w-4 h-4';
		const title = document.createElement('span'); title.className = 'flex-1 min-w-[180px]'; title.textContent = `${item.title} · ${item.copy_id}`;
		const condition = document.createElement('select'); condition.className = 'border rounded-lg p-2 text-sm'; condition.dataset.copyId = item.copy_id;
		for (const [value, label] of [['NORMAL', 'Bình thường'], ['DAMAGED', 'Hư hỏng'], ['LOST', 'Mất']]) {
			const option = document.createElement('option'); option.value = value; option.textContent = label; condition.append(option);
		}
		row.append(check, title, condition); container.append(row);
	}
	if (!pending.length) container.textContent = 'Phiếu này đã trả đủ các bản sao.';
	document.getElementById('submitReturn').disabled = !pending.length;
	panel.classList.remove('hidden');
}

document.getElementById('lookupForm').addEventListener('submit', async event => {
	event.preventDefault(); message.textContent = 'Đang tra cứu...';
	resultsPanel.replaceChildren(); panel.classList.add('hidden');
	const form = new FormData(event.currentTarget);
	const identifier = String(form.get('identifier') || '').trim();
	try {
		if (form.get('search_type') === 'reader') {
			const response = await fetch(`/borrowing/lookup?reader_id=${encodeURIComponent(identifier)}`);
			const result = await response.json();
			if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tra cứu phiếu theo độc giả.');
			if (!result.data.length) { message.textContent = 'Độc giả này chưa có phiếu mượn.'; return; }
			message.textContent = `Tìm thấy ${result.data.length} phiếu mượn. Chọn một phiếu để xử lý:`;
			for (const loan of result.data) {
				const button = document.createElement('button'); button.type = 'button';
				button.className = 'w-full text-left bg-white border rounded-xl p-4 hover:border-blue-400';
				const title = document.createElement('strong'); title.textContent = loan.loan_id;
				const info = document.createElement('span'); info.className = 'block text-sm text-slate-500 mt-1';
				info.textContent = `${loan.full_name} · Mượn ${new Date(loan.borrow_date).toLocaleDateString('vi-VN')} · Hạn ${new Date(loan.due_date).toLocaleDateString('vi-VN')} · Còn ${loan.unreturned_copies}/${loan.total_copies} bản chưa trả`;
				button.append(title, info);
				button.addEventListener('click', async () => {
					try { await loadLoanDetails(loan.loan_id); message.textContent = ''; }
					catch (error) { message.textContent = error.message; }
				});
				resultsPanel.append(button);
			}
		} else {
			await loadLoanDetails(identifier);
			message.textContent = '';
		}
	} catch (error) { panel.classList.add('hidden'); message.textContent = error.message; }
});

document.getElementById('submitReturn').addEventListener('click', async () => {
	if (!currentLoan) return;
	const checked = [...document.querySelectorAll('#returnItems input[type="checkbox"]:checked')];
	const items = checked.map(input => ({
		copy_id: input.value,
		condition: document.querySelector(`select[data-copy-id="${CSS.escape(input.value)}"]`).value,
	}));
	if (!items.length) { message.textContent = 'Chọn ít nhất một bản sao cần ghi nhận trả.'; return; }
	try {
		const response = await fetch('/returns/process', {
			method: 'POST', headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ loan_id: currentLoan.loan_id, items }),
		});
		const result = await response.json();
		if (!response.ok || !result.success) throw new Error(result.message || 'Không thể ghi nhận trả sách.');
		message.className = 'text-sm mt-3 text-emerald-600';
		message.textContent = `${result.message} Tổng phí: ${Number(result.total_charge).toLocaleString('vi-VN')} VND.`;
		await loadLoanDetails(currentLoan.loan_id);
	} catch (error) { message.className = 'text-sm mt-3 text-red-600'; message.textContent = error.message; }
});
