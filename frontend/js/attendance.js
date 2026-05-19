document.addEventListener('DOMContentLoaded', async function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('captureBtn');
    const resultArea = document.getElementById('resultArea');
    const attendanceResult = document.getElementById('attendanceResult');
    const resultIcon = document.getElementById('resultIcon');
    const resultName = document.getElementById('resultName');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');
    const todayAttendance = document.getElementById('todayAttendance');
    const scanLine = document.getElementById('scanLine');
    const waitingText = document.getElementById('waitingText');
    const cameraStatus = document.getElementById('cameraStatus');
    const todayCount = document.getElementById('todayCount');

    let isCameraRunning = false;

    // Auto start camera on load
    try {
        const success = await Shell.startCamera(video, canvas);
        if (success) {
            isCameraRunning = true;
            captureBtn.disabled = false;
            scanLine.style.display = 'block';
        } else {
            setCameraError();
        }
    } catch (err) {
        setCameraError();
    }

    function setCameraError() {
        cameraStatus.className = 'badge bg-danger';
        cameraStatus.innerHTML = '<i class="bi bi-x-circle me-1"></i> Failed';
        video.style.background = '#e2e8f0';
    }

    captureBtn.addEventListener('click', async function() {
        if (!isCameraRunning) return;
        
        const imageData = Shell.captureFrame();
        if (!imageData) {
            Toast.error('Failed to capture image');
            return;
        }

        // UI processing state
        captureBtn.disabled = true;
        const originalBtnText = captureBtn.innerHTML;
        captureBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        scanLine.style.animation = 'scan 0.5s linear infinite';
        waitingText.style.display = 'none';

        try {
            const result = await API.markAttendance(imageData);
            attendanceResult.style.display = 'block';
            
            attendanceResult.className = 'fade-in';
            // force reflow to restart animation
            void attendanceResult.offsetWidth;

            if (result.status === 'success') {
                resultIcon.innerHTML = '<i class="bi bi-check-circle-fill"></i>';
                resultIcon.style.color = '#10b981';
                resultName.textContent = result.name || 'Unknown';
                resultMessage.textContent = 'Attendance marked successfully!';
                resultMessage.className = 'text-success fw-bold';
                resultDetails.innerHTML = `
                    <div class="d-flex justify-content-between mb-2 border-bottom border-secondary pb-1">
                        <span class="text-muted">Roll No:</span><span class="fw-semibold text-white">${result.roll_no || 'N/A'}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Time:</span><span class="fw-semibold text-white">${result.time || new Date().toLocaleTimeString()}</span>
                    </div>
                `;
                Toast.success('Attendance marked for ' + (result.name || 'Unknown'));
            } else if (result.status === 'unknown') {
                resultIcon.innerHTML = '<i class="bi bi-person-x-fill"></i>';
                resultIcon.style.color = '#ef4444';
                resultName.textContent = 'Unknown Person';
                resultMessage.textContent = 'Face not recognized. Please register first.';
                resultMessage.className = 'text-danger fw-bold';
                resultDetails.innerHTML = '';
                Toast.warning('Face not recognized.');
            } else {
                resultIcon.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i>';
                resultIcon.style.color = '#f59e0b';
                resultName.textContent = result.name || 'Already Marked';
                resultMessage.textContent = result.message || 'Attendance already recorded today.';
                resultMessage.className = 'text-warning fw-bold';
                resultDetails.innerHTML = `
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Time:</span><span class="fw-semibold text-white">${result.time || ''}</span>
                    </div>
                `;
                Toast.info('Already marked today.');
            }

            loadTodayAttendance();
        } catch (err) {
            resultIcon.innerHTML = '<i class="bi bi-x-circle-fill"></i>';
            resultIcon.style.color = '#ef4444';
            resultName.textContent = 'Error';
            resultMessage.textContent = err.message;
            resultMessage.className = 'text-danger fw-bold';
            resultDetails.innerHTML = '';
            attendanceResult.style.display = 'block';
            Toast.error('Failed to mark attendance.');
        }

        // Restore UI
        captureBtn.disabled = false;
        captureBtn.innerHTML = originalBtnText;
        scanLine.style.animation = 'scan 2s linear infinite';
    });

    async function loadTodayAttendance() {
        try {
            const data = await API.getTodayAttendance();
            if (data.records && data.records.length > 0) {
                todayCount.textContent = data.records.length;
                let html = '<div class="list-group list-group-flush">';
                data.records.forEach(record => {
                    html += `
                        <div class="list-group-item d-flex justify-content-between align-items-center px-1">
                            <div class="d-flex align-items-center">
                                <div class="bg-dark rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 40px; height: 40px; border: 1px solid rgba(255,255,255,0.1);">
                                    <i class="bi bi-person text-secondary"></i>
                                </div>
                                <div>
                                    <strong class="d-block text-white">${record.name}</strong>
                                    <small class="text-muted">${record.roll_no || 'Unknown'}</small>
                                </div>
                            </div>
                            <span class="badge bg-success rounded-pill px-3 py-2">${record.time || ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
                todayAttendance.innerHTML = html;
            } else {
                todayCount.textContent = '0';
                todayAttendance.innerHTML = '<div class="text-center py-4 text-muted"><i class="bi bi-inbox fs-1 d-block mb-2 opacity-50"></i>No attendance records yet today.</div>';
            }
        } catch (err) {
            todayAttendance.innerHTML = '<p class="text-danger mb-0 text-center py-3">Failed to load records.</p>';
            console.error('Failed to load today attendance:', err);
        }
    }

    loadTodayAttendance();
    
    // Cleanup on page leave
    window.addEventListener('beforeunload', () => {
        if (isCameraRunning) {
            Shell.stopCamera();
        }
    });
});
