const API = {
    get BASE() { return CONFIG.API_BASE_URL; },

    headers(json = true) {
        const h = {};
        if (json) h['Content-Type'] = 'application/json';
        const tok = localStorage.getItem('scanora_token');
        if (tok) h['Authorization'] = `Bearer ${tok}`;
        return h;
    },

    async request(endpoint, options = {}) {
        const url = `${this.BASE}${endpoint}`;
        const res = await fetch(url, {
            headers: { ...this.headers(), ...options.headers },
            ...options,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        return data;
    },

    // ── Auth ──────────────────────────────────────────────────────────
    login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
    },

    getMe() { return this.request('/auth/me'); },

    // ── Courses ────────────────────────────────────────────────────────
    getCourses() { return this.request('/courses'); },

    // ── Student registration (multipart) ──────────────────────────────
    registerUser(formData) {
        return fetch(`${this.BASE}/register`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('scanora_token') || ''}` },
            body: formData,
        }).then(async r => {
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || 'Registration failed');
            return d;
        });
    },

    // ── Face scan (public) ────────────────────────────────────────────
    scan(lectureId, imageData) {
        return this.request('/scan', {
            method: 'POST',
            body: JSON.stringify({ lecture_id: lectureId, image: imageData }),
        });
    },

    // ── Public lectures for scanner ────────────────────────────────────
    getTodayLectures(courseId) {
        const q = courseId ? `?course_id=${courseId}` : '';
        return this.request(`/lectures/today${q}`);
    },

    // ── Admin ──────────────────────────────────────────────────────────
    admin: {
        getStats() { return API.request('/admin/stats'); },
        getTrends(days = 7) { return API.request(`/admin/stats/trends?days=${days}`); },
        getProfessors() { return API.request('/admin/professors'); },
        addProfessor(data) { return API.request('/admin/professors', { method: 'POST', body: JSON.stringify(data) }); },
        deleteProfessor(id) { return API.request(`/admin/professors/${id}`, { method: 'DELETE' }); },
        updateProfessorCourses(id, courseIds) {
            return API.request(`/admin/professors/${id}/courses`, { method: 'PUT', body: JSON.stringify({ course_ids: courseIds }) });
        },
        getStudents() { return API.request('/admin/students'); },
        deleteStudent(id) { return API.request(`/admin/students/${id}`, { method: 'DELETE' }); },
        getLectures(dateStr) {
            const q = dateStr ? `?date=${dateStr}` : '';
            return API.request(`/admin/lectures${q}`);
        },
        getAttendance(params = {}) {
            const q = new URLSearchParams(params).toString();
            return API.request(`/admin/attendance${q ? '?' + q : ''}`);
        },
        markAttendance(data) { return API.request('/admin/attendance', { method: 'POST', body: JSON.stringify(data) }); },
        updateAttendance(id, data) { return API.request(`/admin/attendance/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
        deleteAttendance(id) { return API.request(`/admin/attendance/${id}`, { method: 'DELETE' }); },
    },

    // ── Professor ──────────────────────────────────────────────────────
    professor: {
        getStats() { return API.request('/professor/stats'); },
        createLecture(data) { return API.request('/professor/lectures', { method: 'POST', body: JSON.stringify(data) }); },
        getLectures(dateStr) {
            const q = dateStr ? `?date=${dateStr}` : '';
            return API.request(`/professor/lectures${q}`);
        },
        getLectureAttendance(lectureId) { return API.request(`/professor/lectures/${lectureId}/attendance`); },
        reviewAttendance(id, status) {
            return API.request(`/professor/attendance/${id}`, { method: 'PUT', body: JSON.stringify({ status }) });
        },
    },

    // ── Student ────────────────────────────────────────────────────────
    student: {
        getMyLectures() { return API.request('/student/lectures'); },
        getMyAttendance() { return API.request('/student/attendance'); },
    },

    // ── Legacy compat for existing attendance.js + index stats ─────────
    markAttendance(imageData) {
        return this.request('/scan', {
            method: 'POST',
            body: JSON.stringify({ image: imageData, lecture_id: window._activeLectureId || null }),
        });
    },

    getAttendance(dateStr = '') {
        const params = dateStr ? `?date=${dateStr}` : '';
        return this.request(`/admin/attendance${params}`);
    },

    getStudents() { return this.request('/admin/students'); },

    getStats() { return this.request('/stats'); },

    getTodayAttendance() {
        const today = new Date().toISOString().split('T')[0];
        return this.request(`/admin/attendance?date=${today}`);
    },
};
