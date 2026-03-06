// ── COMPANY METHODS


const companyMethods = {
    async loadMyCompany(userId) {
        const res = await fetch(`/api/company/profile/${userId}`);
        if (res.ok) this.myCompany = await res.json();
    },
    async loadMyDrives() {
        if (!this.myCompany) return;
        const res = await fetch(`/api/company/drives/${this.myCompany.id}`);
        if (res.ok) this.myDrives = await res.json();
    },
    async loadMyApplications() {
        if (!this.myCompany) return;
        const res = await fetch(`/api/company/applications/${this.myCompany.id}`);
        if (res.ok) this.myApplications = await res.json();
    },
    async createDrive() {
        this.driveErr = ''; this.driveOk = '';
        const res = await fetch('/api/company/drive/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...this.df, company_id: this.myCompany.id })
        });
        const data = await res.json();
        if (res.ok) {
            this.driveOk = data.message;
            this.df = { title: '', description: '', eligible_branch: '', eligible_cgpa: '', eligible_year: '', deadline: '' };
        } else {
            this.driveErr = data.message;
        }
    },
    async updateAppStatus(appId, status) {
        await fetch(`/api/company/application/${appId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        this.loadMyApplications();
    }
};