(async function renderReports() {
  if (typeof Chart === 'undefined') return;
  try {
    const [activityResponse, categoryResponse] = await Promise.all([
      fetch('/admin/reports/activity?days=7'),
      fetch('/admin/reports/categories')
    ]);
    const activity = await activityResponse.json();
    const categories = await categoryResponse.json();
    const activityCanvas = document.getElementById('activityChart');
    if (activity.success && activityCanvas) {
      // Destroy an existing instance before re-initializing the same canvas.
      Chart.getChart(activityCanvas)?.destroy();
      new Chart(activityCanvas, {
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
    const categoryCanvas = document.getElementById('categoryChart');
    if (categories.success && categoryCanvas) {
      // Keep chart initialization idempotent when this script is loaded again.
      Chart.getChart(categoryCanvas)?.destroy();
      new Chart(categoryCanvas, {
        type: 'doughnut',
        data: { labels: categories.data.map(item => item.category), datasets: [{ data: categories.data.map(item => item.copies) }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
      });
    }
  } catch (error) { console.error('Không thể tải dữ liệu báo cáo:', error); }
})();
