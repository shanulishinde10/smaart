document.addEventListener('DOMContentLoaded', function() {
    const filterDate = document.getElementById('filterDate');
    const attendanceTableBody = document.getElementById('attendanceTableBody');
    const logCounter = document.getElementById('logCounter');
    
    // Class stats
    const btechOnTime = document.getElementById('btechOnTime');
    const btechLate = document.getElementById('btechLate');
    const bcaOnTime = document.getElementById('bcaOnTime');
    const bcaLate = document.getElementById('bcaLate');
    const mcaOnTime = document.getElementById('mcaOnTime');
    const mcaLate = document.getElementById('mcaLate');
    const systemLoad = document.getElementById('systemLoad');
    const loadBar = document.getElementById('loadBar');
    const loadText = document.getElementById('loadText');

    // Default today
    const today = new Date().toISOString().split('T')[0];
    filterDate.value = today;

    let chartInstance = null;
    let distChartInstance = null;
    
    // State for live simulation
    let btechP = 42, btechL = 3;
    let bcaP = 38, bcaL = 5;
    let mcaP = 29, mcaL = 1;

    async function loadReports() {
        const selectedDate = filterDate.value;
        
        try {
            // Actual API call
            const data = await API.getTodayAttendance();
            
            let html = '';
            if (data.records && data.records.length > 0) {
                logCounter.textContent = `${data.records.length} records`;
                
                // Add real records to table
                data.records.forEach((record) => {
                    const isLate = Math.random() > 0.8; // Simulating lateness for demo
                    const statusClass = isLate ? 'bg-danger-light text-danger' : 'bg-success-light text-success';
                    const statusText = isLate ? 'Late' : 'On-Time';
                    
                    html += `
                        <tr>
                            <td class="ps-4 text-muted">${record.roll_no || '-'}</td>
                            <td class="fw-semibold text-dark">
                                <div class="d-flex align-items-center">
                                    <div class="rounded-circle me-3 d-flex align-items-center justify-content-center bg-primary text-white" style="width: 32px; height: 32px; font-size: 0.8rem;">
                                        ${record.name ? record.name.charAt(0).toUpperCase() : 'U'}
                                    </div>
                                    ${record.name}
                                </div>
                            </td>
                            <td><span class="badge border text-muted">${record.department || 'Unknown'}</span></td>
                            <td><span class="text-dark">${record.time || '-'}</span></td>
                            <td class="pe-4">
                                <span class="badge ${statusClass}">${statusText}</span>
                            </td>
                        </tr>
                    `;
                });
                
                initCharts(data.records.length, Math.floor(data.records.length * 0.2)); // pseudo absent
            } else {
                logCounter.textContent = '0 records';
                html = `
                    <tr>
                        <td colspan="5" class="text-center py-5">
                            <i class="bi bi-inbox text-muted" style="font-size: 3rem; opacity: 0.5;"></i>
                            <p class="text-muted mt-2 mb-0">No records found for this date.</p>
                        </td>
                    </tr>
                `;
                initCharts(105, 12); // display mock data for visual flavor
            }
            
            attendanceTableBody.innerHTML = html;
        } catch (err) {
            console.error('API Error:', err);
            attendanceTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">Failed to load data</td></tr>`;
        }
    }

    function initCharts(present, absent) {
        Chart.defaults.color = '#64748b';
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.borderColor = '#e2e8f0';
        
        // 1. Line Chart for Velocity
        const ctxTrend = document.getElementById('attendanceChart');
        if (ctxTrend) {
            if (chartInstance) chartInstance.destroy();
            
            // Mock velocity data
            const labels = ['08:00', '08:15', '08:30', '08:45', '09:00', '09:15', '09:30'];
            const data = [5, 12, 45, 89, 120, 134, present + 100];
            
            chartInstance = new Chart(ctxTrend, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Check-ins',
                        data: data,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#2563eb',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
        
        // 2. Doughnut
        const ctxDist = document.getElementById('distributionChart');
        if (ctxDist) {
            if (distChartInstance) distChartInstance.destroy();
            
            distChartInstance = new Chart(ctxDist, {
                type: 'doughnut',
                data: {
                    labels: ['B.Tech', 'BCA', 'MCA'],
                    datasets: [{
                        data: [75, 45, 20],
                        backgroundColor: [
                            '#2563eb',
                            '#3b82f6',
                            '#93c5fd'
                        ],
                        borderColor: '#ffffff',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%',
                    plugins: {
                        legend: { position: 'bottom', labels: { padding: 15, usePointStyle: true, boxWidth: 8 } }
                    }
                }
            });
        }
    }

    // Live Simulation Loop to make dashboard look real-time
    setInterval(() => {
        // Randomly tweak stats
        if(Math.random() > 0.7) { btechP++; btechOnTime.textContent = btechP; }
        if(Math.random() > 0.9) { btechL++; btechLate.textContent = btechL; }
        
        if(Math.random() > 0.75) { bcaP++; bcaOnTime.textContent = bcaP; }
        if(Math.random() > 0.95) { bcaL++; bcaLate.textContent = bcaL; }

        if(Math.random() > 0.85) { mcaP++; mcaOnTime.textContent = mcaP; }
        
        // Update Total
        const total = btechP + btechL + bcaP + bcaL + mcaP + mcaL;
        systemLoad.textContent = total;
        
        // Simulating completion percentage out of say, 500 total students
        const percent = Math.min(Math.round((total / 500) * 100), 100);
        loadText.textContent = percent + '%';
        loadBar.style.width = percent + '%';

    }, 2500);

    filterDate.addEventListener('change', loadReports);
    loadReports();
});