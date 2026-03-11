const studentMethods = {
    async loadMyProfile(userId) {
        const res = await fetch(`/api/student/profile/${userId}`);

        if (res.ok) this.myProfile = await res.json();
    },

    async updateProfile() {
        const res = await fetch(`/api/student/profile/update/${this.myProfile.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.editProfile)
        });

        const data = await res.json();
        this.profileMsg = data.message;
        this.profileMsgOk = res.ok;
        if (res.ok) {
            this.myProfile = { ...this.myProfile, ...this.editProfile };
            this.showEditProfile = false;
        }
    },

    async loadApprovedDrives() {
        const res = await fetch('/api/student/drives');
        if (res.ok) {
            this.approvedDrives = await res.json();
            this.filteredDrives = this.approvedDrives;
        }
    },
    filterDrives() {
        this.filteredDrives = this.approvedDrives.filter(d =>
            d.title.toLowerCase().includes(this.dsearch.toLowerCase())
        );
    },
    async applyDrive(driveId) {
        this.applyErr = ''; this.applyOk = '';
        const res = await fetch('/api/student/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ drive_id: driveId, student_id: this.myProfile.id })
        });

        const data = await res.json();
        
        if (res.ok) { this.applyOk = 'Applied successfully!'; }
        else { this.applyErr = data.message; }
    },
    async loadMyStudentApps() {
        if (!this.myProfile) return;
        const res = await fetch(`/api/student/applications/${this.myProfile.id}`);
        if (res.ok) this.myStudentApps = await res.json();
    },
    
    async loadStudentPlacements() {
        if (!this.myProfile) return;
        const res = await fetch(`/api/student/placements/${this.myProfile.id}`);
        if (res.ok) this.myStudentPlacements = await res.json();
    },

    async exportCSV() {
        const res = await fetch(`/api/student/export/${this.myProfile.id}`, { method: 'POST' });
        const data = await res.json();
        this.exportMsg = data.message;
    },
};