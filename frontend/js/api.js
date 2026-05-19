const API = {
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        };
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Request failed');
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    registerUser(formData) {
        return fetch(`${CONFIG.API_BASE_URL}/register`, {
            method: 'POST',
            body: formData
        }).then(async r => {
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || 'Registration failed');
            return d;
        });
    },

    markAttendance(imageData) {
        return this.request('/attendance', {
            method: 'POST',
            body: JSON.stringify({ image: imageData })
        });
    },

    getAttendance(date = '') {
        const params = date ? `?date=${date}` : '';
        return this.request(`/attendance${params}`);
    },

    getStudents() {
        return this.request('/students');
    },

    getStats() {
        return this.request('/stats');
    },

    getTodayAttendance() {
        const today = new Date().toISOString().split('T')[0];
        return this.request(`/attendance/date/${today}`);
    }
};