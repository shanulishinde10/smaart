document.addEventListener('DOMContentLoaded', async function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const registerForm = document.getElementById('registerForm');
    const registerBtn = document.getElementById('registerBtn');
    const registerBtnText = document.getElementById('registerBtnText');
    const registerSpinner = document.getElementById('registerSpinner');
    const captureBtn = document.getElementById('captureBtn');
    const capturedPreview = document.getElementById('capturedPreview');
    const capturedImg = document.getElementById('capturedImg');
    const cameraStatus = document.getElementById('cameraStatus');
    const scanLine = document.getElementById('scanLine');
    const videoWrapper = document.getElementById('videoWrapper');

    let isCameraRunning = false;
    let capturedImageData = null;

    // Auto-start camera
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

    captureBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (capturedImageData) {
            // It's in recapture mode
            capturedImageData = null;
            capturedPreview.style.display = 'none';
            videoWrapper.style.opacity = '1';
            captureBtn.innerHTML = '<i class="bi bi-camera me-2"></i> Capture Face';
            captureBtn.className = 'btn btn-secondary w-100 py-2';
            scanLine.style.display = 'block';
            checkFormComplete();
            return;
        }

        // Capture mode
        const imageData = Shell.captureFrame();
        if (imageData) {
            capturedImageData = imageData;
            capturedImg.src = imageData;
            capturedPreview.style.display = 'block';
            videoWrapper.style.opacity = '0.3';
            scanLine.style.display = 'none';
            captureBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise me-2"></i> Recapture';
            captureBtn.className = 'btn btn-warning w-100 py-2 text-dark';
            checkFormComplete();
            Toast.success('Face captured successfully.');
        } else {
            Toast.error('Failed to capture face.');
        }
    });

    function checkFormComplete() {
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const rollNo = document.getElementById('rollNo').value.trim();
        const department = document.getElementById('department').value.trim();
        
        if (name && email && rollNo && department && capturedImageData) {
            registerBtn.disabled = false;
            registerBtn.classList.remove('btn-secondary');
            registerBtn.classList.add('btn-primary');
        } else {
            registerBtn.disabled = true;
        }
    }

    ['name', 'email', 'rollNo', 'department'].forEach(id => {
        document.getElementById(id).addEventListener('input', checkFormComplete);
    });

    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const rollNo = document.getElementById('rollNo').value.trim();
        const department = document.getElementById('department').value.trim();

        if (!capturedImageData) {
            Toast.warning('Please capture a face image first.');
            return;
        }

        registerBtn.disabled = true;
        registerBtnText.textContent = 'Registering...';
        registerSpinner.classList.remove('d-none');

        const formData = new FormData();
        formData.append('name', name);
        formData.append('email', email);
        formData.append('roll_no', rollNo);
        formData.append('department', department);
        const blob = Shell.dataURLToBlob(capturedImageData);
        formData.append('image', blob, 'face.jpg');

        try {
            const result = await API.registerUser(formData);
            Toast.success(`Registration successful! User ID: ${result.id}`);
            
            // Reset form
            registerForm.reset();
            capturedImageData = null;
            capturedPreview.style.display = 'none';
            videoWrapper.style.opacity = '1';
            captureBtn.innerHTML = '<i class="bi bi-camera me-2"></i> Capture Face';
            captureBtn.className = 'btn btn-secondary w-100 py-2';
            scanLine.style.display = 'block';
            
        } catch (err) {
            Toast.error('Registration failed: ' + err.message);
        }

        registerBtn.disabled = true;
        registerBtnText.textContent = 'Register & Save Profile';
        registerSpinner.classList.add('d-none');
    });

    // Cleanup on page leave
    window.addEventListener('beforeunload', () => {
        if (isCameraRunning) {
            Shell.stopCamera();
        }
    });
});
