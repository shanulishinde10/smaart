const Shell = {
    video: null,
    canvas: null,
    stream: null,
    capturedImage: null,

    async startCamera(videoEl, canvasEl) {
        this.video = videoEl;
        this.canvas = canvasEl;
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
            this.video.srcObject = this.stream;
            await this.video.play();
            return true;
        } catch (err) {
            console.error('Camera error:', err);
            if (typeof Toast !== 'undefined') {
                Toast.error('Unable to access camera. Please allow camera permissions.');
            } else {
                alert('Unable to access camera. Please allow camera permissions.');
            }
            return false;
        }
    },

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.video) this.video.srcObject = null;
    },

    captureFrame() {
        if (!this.video || !this.canvas) return null;
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const ctx = this.canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0);
        this.capturedImage = this.canvas.toDataURL('image/jpeg', 0.8);
        return this.capturedImage;
    },

    dataURLToBlob(dataURL) {
        const parts = dataURL.split(',');
        const mime = parts[0].match(/:(.*?);/)[1];
        const bytes = atob(parts[1]);
        const ab = new ArrayBuffer(bytes.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < bytes.length; i++) ia[i] = bytes.charCodeAt(i);
        return new Blob([ab], { type: mime });
    }
};
