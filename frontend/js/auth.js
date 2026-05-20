const Auth = {
    TOKEN_KEY: 'smaart_token',
    USER_KEY: 'smaart_user',
    PROFILE_KEY: 'smaart_profile',

    getToken() { return localStorage.getItem(this.TOKEN_KEY); },
    getUser() {
        const u = localStorage.getItem(this.USER_KEY);
        return u ? JSON.parse(u) : null;
    },
    getProfile() {
        const p = localStorage.getItem(this.PROFILE_KEY);
        return p ? JSON.parse(p) : null;
    },

    setAuth(token, user, profile) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        if (profile) localStorage.setItem(this.PROFILE_KEY, JSON.stringify(profile));
    },

    clearAuth() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        localStorage.removeItem(this.PROFILE_KEY);
    },

    isLoggedIn() { return !!this.getToken(); },

    requireRole(allowedRoles) {
        if (!this.isLoggedIn()) {
            window.location.href = 'login.html';
            return false;
        }
        const user = this.getUser();
        if (allowedRoles && !allowedRoles.includes(user.role)) {
            window.location.href = this.roleHome(user.role);
            return false;
        }
        return true;
    },

    roleHome(role) {
        if (role === 'admin') return 'admin.html';
        if (role === 'professor') return 'professor.html';
        if (role === 'student') return 'student.html';
        return 'login.html';
    },

    logout() {
        this.clearAuth();
        window.location.href = 'login.html';
    },

    // Sidebar nav configs per role
    _navLinks: {
        admin: [
            { href: 'admin.html',            icon: 'bi-speedometer2',    label: 'Dashboard' },
            { href: 'admin-professors.html',  icon: 'bi-person-video2',   label: 'Professors' },
            { href: 'admin-students.html',    icon: 'bi-mortarboard',     label: 'Students' },
            { href: 'admin-attendance.html',  icon: 'bi-calendar-check',  label: 'Attendance' },
            { href: 'admin-lectures.html',    icon: 'bi-easel',           label: 'Lectures' },
            { href: 'attendance.html',        icon: 'bi-camera',          label: 'Scanner' },
        ],
        professor: [
            { href: 'professor.html',   icon: 'bi-easel',          label: 'My Lectures' },
            { href: 'attendance.html',  icon: 'bi-camera',         label: 'Scanner' },
        ],
        student: [
            { href: 'student.html',     icon: 'bi-person-check',   label: 'My Attendance' },
            { href: 'attendance.html',  icon: 'bi-camera',         label: 'Scanner' },
        ],
    },

    renderSidebar() {
        const user = this.getUser();
        if (!user) return;

        const nav = document.querySelector('.sidebar-nav');
        if (!nav) return;

        const currentPage = location.pathname.split('/').pop() || 'index.html';
        const links = this._navLinks[user.role] || this._navLinks.student;

        nav.innerHTML = links.map(l => `
            <a class="nav-link ${currentPage === l.href ? 'active' : ''}" href="${l.href}">
                <i class="bi ${l.icon}"></i> ${l.label}
            </a>
        `).join('');

        // User pill in sidebar footer
        const footer = document.querySelector('.sidebar-footer');
        if (footer && !footer.querySelector('.user-pill')) {
            const colors = { admin: 'var(--pink)', professor: 'var(--cyan)', student: 'var(--green)' };
            const color = colors[user.role] || 'var(--purple)';
            const pill = document.createElement('div');
            pill.className = 'user-pill';
            pill.style.cssText = `display:flex;align-items:center;gap:8px;padding:0.6rem 0.75rem;background:var(--bg-elevated);border-radius:var(--r-md);border:1px solid var(--border);margin-bottom:0.75rem;font-size:0.78rem;`;
            pill.innerHTML = `
                <div style="width:30px;height:30px;border-radius:50%;background:${color}22;border:1.5px solid ${color}55;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <i class="bi bi-person-fill" style="font-size:0.8rem;color:${color};"></i>
                </div>
                <div style="overflow:hidden;flex:1;">
                    <div style="font-weight:700;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${user.username}</div>
                    <div style="color:${color};font-size:0.68rem;font-weight:600;text-transform:capitalize;">${user.role}</div>
                </div>
                <button onclick="Auth.logout()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px;border-radius:6px;transition:color 0.15s;" title="Logout"
                    onmouseover="this.style.color='var(--red)'" onmouseout="this.style.color='var(--text-muted)'">
                    <i class="bi bi-box-arrow-right"></i>
                </button>
            `;
            footer.prepend(pill);
        }
    }
};
