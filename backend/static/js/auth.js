const authMethods = {
    async login() {
        this.loading = true; this.msg = '';
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.lf)
        });
        const data = await res.json();
        if (res.ok) {
            this.currentUser = data;
            this.redirectByRole(data.role, data.user_id);
        } else {
            this.msg = data.message; this.msgOk = false;
        }
        this.loading = false;
    },

    async registerStudent() {
        this.loading = true; this.msg = '';
        const res = await fetch('/api/register/student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.sf)
        });
        const data = await res.json();
        this.msg = data.message; this.msgOk = res.ok;
        if (res.ok) this.tab = 'login';
        this.loading = false;
    },

    async registerCompany() {
        this.loading = true; this.msg = '';
        const res = await fetch('/api/register/company', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.cf)
        });
        const data = await res.json();
        this.msg = data.message; this.msgOk = res.ok;
        if (res.ok) this.tab = 'login';
        this.loading = false;
    },

    async redirectByRole(role, userId) {
    if (role === 'admin') {
        this.page = 'admin';
        this.loadStats();
    } else if (role === 'company') {
        const res = await fetch(`/api/company/profile/${userId}`);
        if (res.ok) { this.myCompany = await res.json(); }  
        this.page = 'company';
    } else if (role === 'student') {
        const res = await fetch(`/api/student/profile/${userId}`);
        if (res.ok) { this.myProfile = await res.json(); } 
        this.page = 'student';
        this.loadApprovedDrives();
    }
},

    async logout() {
        await fetch('/api/logout', { method: 'POST' });
        this.currentUser = null;
        this.page = 'login';
        this.msg = '';
    },

    forceLogout() {
        this.currentUser = null;
        this.page = 'login';
        this.msg = 'Session expired. Please login again.';
        this.msgOk = false;
    },

    async checkSession() {
        try {
            const res = await fetch('/api/verify');
            if (res.ok) {
                const data = await res.json();
                this.currentUser = data;
                await this.redirectByRole(data.role, data.user_id);
            } else {
                this.page = 'login';
            }
        } catch(e) {
            this.page = 'login';
        }
    }
};