(async function renderReports() {
	if (typeof Chart === 'undefined') return;
	try {
		const [activityResponse, categoryResponse] = await Promise.all([
			fetch('/admin/reports/activity?days=7'),
			fetch('/admin/reports/categories')
		]);
		const activity = await activityResponse.json();
		const categories = await categoryResponse.json();
		if (activity.success && document.getElementById('activityChart')) {
			new Chart(document.getElementById('activityChart'), {
				type: 'line',
				data: {
					labels: activity.data.map(item => new Date(`${item.date}T00:00:00`).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })),
					datasets: [
						{ label: 'Bản sao mượn', data: activity.data.map(item => item.borrowed), tension: 0.3 },
						{ label: 'Lượt trả', data: activity.data.map(item => item.returned), tension: 0.3 }
					]
				},
				options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
			});
		}
		if (categories.success && document.getElementById('categoryChart')) {
			new Chart(document.getElementById('categoryChart'), {
				type: 'doughnut',
				data: { labels: categories.data.map(item => item.category), datasets: [{ data: categories.data.map(item => item.copies) }] },
				options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
			});
		}
	} catch (error) { console.error('Không thể tải dữ liệu báo cáo:', error); }
})();
