const studentMethods = {
    async loadMyProfile(userId) {
        const res = await fetch(`/api/student/profile/${userId}`);
        if (res.ok) this.myProfile = await res.json();
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
    }
};