async function postAction(url, body = {}) {
	const response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(body), cache: 'no-store' });
	const result = await response.json().catch(() => ({}));
	if (!response.ok || !result.success) throw new Error(result.message || 'Không thể thực hiện thao tác.');
	return result;
}
const actionMessage = document.getElementById('loanActionMessage');
document.addEventListener('click', async event => {
	const returnButton = event.target.closest('.requestReturn');
	const cancelReturn = event.target.closest('.cancelReturnRequest');
	const cancelBorrow = event.target.closest('.cancelBorrowRequest');
	const button = returnButton || cancelReturn || cancelBorrow;
	if (!button) return;
	const originalText = button.textContent;
	button.disabled = true;
	actionMessage.className = 'text-sm mt-3 text-slate-500';
	actionMessage.textContent = 'Đang xử lý...';
	try {
		if (returnButton) await postAction('/profile/api/return-requests', { detail_id: Number(button.dataset.detailId) });
		else if (cancelReturn) await postAction(`/profile/api/return-requests/${encodeURIComponent(button.dataset.id)}/cancel`);
		else await postAction(`/profile/api/borrow-requests/${encodeURIComponent(button.dataset.id)}/cancel`);
		actionMessage.className = 'text-sm mt-3 text-emerald-600';
		actionMessage.textContent = returnButton ? 'Đã gửi yêu cầu trả sách.' : 'Đã hủy yêu cầu.';
		window.location.reload();
	} catch (error) {
		button.disabled = false;
		button.textContent = originalText;
		actionMessage.className = 'text-sm mt-3 text-red-600';
		actionMessage.textContent = error.message;
	}
});
