async function loadFines() {
	const rows = document.getElementById('fineRows'); rows.replaceChildren();
	try {
		const response = await fetch('/api/fines/outstanding'); const result = await response.json(); if (!response.ok || !result.success) throw new Error(result.message || 'Không thể tải khoản phí.');
		for (const item of result.data) {
			const tr = document.createElement('tr'); tr.className = 'border-b last:border-0';
			const values = [item.full_name, `${item.title} · ${item.copy_id}`, `${Number(item.overdue_fine).toLocaleString('vi-VN')} đ`, `${Number(item.compensation).toLocaleString('vi-VN')} đ`, `${Number(item.paid_amount).toLocaleString('vi-VN')} đ`, `${Number(item.outstanding).toLocaleString('vi-VN')} đ`];
			values.forEach((value, index) => { const td = document.createElement('td'); td.className = 'py-3 pr-3'; td.textContent = value; if (index === 5) td.className += ' font-semibold text-red-600'; tr.append(td); });
			const action = document.createElement('td'); const pay = document.createElement('button'); pay.className = 'bg-blue-600 text-white rounded-lg px-3 py-2'; pay.textContent = 'Thu đủ'; pay.onclick = () => payFine(item.detail_id, item.outstanding); action.append(pay); tr.append(action); rows.append(tr);
		}
		if (!result.data.length) rows.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-400">Không có khoản phí chưa thanh toán.</td></tr>';
	} catch (error) { document.getElementById('fineMessage').textContent = error.message; }
}
async function payFine(detailId, amount) {
	if (!confirm(`Ghi nhận thanh toán ${Number(amount).toLocaleString('vi-VN')} VND?`)) return;
	try {
		const response = await fetch('/api/fines/payments', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ detail_id: detailId, amount, payment_method: 'CASH' }) });
		const result = await response.json(); if (!response.ok || !result.success) throw new Error(result.message || 'Thanh toán thất bại.');
		document.getElementById('fineMessage').textContent = result.message; await loadFines();
	} catch (error) { document.getElementById('fineMessage').textContent = error.message; }
}
document.getElementById('reloadFines').addEventListener('click', loadFines); loadFines();
