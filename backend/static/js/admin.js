const adminMethods = {
    async loadStats() {
        this.stats = await (await fetch('/api/admin/dashboard')).json();
    },
    async loadCompanies() {
        this.companies = await (await fetch('/api/admin/companies')).json();
    },
    async loadStudents() {
        this.students = await (await fetch('/api/admin/students')).json();
    },
    async loadDrives() {
        this.drives = await (await fetch('/api/admin/drives')).json();
    },
    async loadApplications() {
        this.applications = await (await fetch('/api/admin/applications')).json();
    },
    async approveCompany(id, status) {
        await fetch(`/api/admin/company/${id}/approve`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        this.loadCompanies();
    },
    async approveDrive(id, status) {
        await fetch(`/api/admin/drive/${id}/approve`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        this.loadDrives();
    },
    async blacklistStudent(id, val) {
        await fetch(`/api/admin/student/${id}/blacklist`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_blacklisted: val })
        });
        this.loadStudents();
    },
    async blacklistCompany(id, val) {
        await fetch(`/api/admin/company/${id}/blacklist`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_blacklisted: val })
        });
        this.loadCompanies();
    },
    async search() {
        this.sr = await (await fetch(`/api/admin/search?q=${this.sq}&type=${this.st}`)).json();
    }
};