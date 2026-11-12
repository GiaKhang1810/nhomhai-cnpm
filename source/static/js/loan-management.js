async function requestAction(url, message) {
	const response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({}), cache: 'no-store' });
	const result = await response.json().catch(() => ({}));
	if (!response.ok || !result.success) throw new Error(result.message || message || 'Thao tác thất bại.');
	return result;
}
const notice = document.getElementById('loanManagementMessage');
document.addEventListener('click', async event => {
	const button = event.target.closest('.approveBorrow, .rejectBorrow, .rejectReturn');
	if (!button) return;
	const id = button.dataset.id;
	let url;
	if (button.classList.contains('approveBorrow')) url = `/borrowing/requests/${encodeURIComponent(id)}/approve`;
	else if (button.classList.contains('rejectBorrow')) url = `/borrowing/requests/${encodeURIComponent(id)}/reject`;
	else url = `/returns/requests/${encodeURIComponent(id)}/reject`;
	const isReject = !button.classList.contains('approveBorrow');
	if (isReject && !window.confirm('Bạn có chắc muốn từ chối yêu cầu này?')) return;
	if (!isReject && !window.confirm('Duyệt yêu cầu và tạo phiếu mượn 14 ngày?')) return;
	button.disabled = true;
	try {
		const result = await requestAction(url);
		notice.className = 'text-sm mt-3 text-emerald-600'; notice.textContent = result.message;
		window.location.reload();
	} catch (error) {
		button.disabled = false; notice.className = 'text-sm mt-3 text-red-600'; notice.textContent = error.message;
	}
});
const filter = document.getElementById('loanFilter');
filter?.addEventListener('input', () => {
	const query = filter.value.trim().toLocaleLowerCase('vi');
	document.querySelectorAll('.loanRow').forEach(row => { row.hidden = !row.textContent.toLocaleLowerCase('vi').includes(query); });
});
