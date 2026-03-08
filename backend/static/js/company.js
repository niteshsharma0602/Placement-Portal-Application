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
    async loadCompanyPlacements() {
        if (!this.myCompany) return;
        const res = await fetch(`/api/company/placements/${this.myCompany.id}`);
        if (res.ok) this.myPlacements = await res.json();
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

    async closeDrive(driveId) {
        await fetch(`/api/company/drive/${driveId}/close`, { method: 'PUT' });
        this.loadMyDrives();
    },

    async updateAppStatus(appId, status) {
        await fetch(`/api/company/application/${appId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        this.loadMyApplications();
    },
    
    async scheduleInterview(appId) {
        const date = this.interviewDates[appId];
        if (!date) {
            alert('Please pick an interview date first.');
            return;
        }
        await fetch(`/api/company/application/${appId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'interview', interview_date: date })
        });
        this.interviewDates[appId] = '';
        this.loadMyApplications();
    },

    async exportCompanyCSV() {
        const res = await fetch(`/api/company/export/${this.myCompany.id}`, { method: 'POST' });
        const data = await res.json();
        this.exportCompanyMsg = data.message;
    },
};