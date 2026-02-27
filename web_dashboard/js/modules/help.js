// help.js - Help page management module (v2 — downloadable report file)
// =====================================================================

'use strict';

class HelpManager {
    constructor() {
        this.currentView = 'menu';
    }

    initHelpHandlers() {
        const helpButtons = document.querySelectorAll('.help-btn');
        helpButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const helpType = e.target.getAttribute('data-help');
                this.showHelpDetail(helpType);
            });
        });

        const backBtn = document.getElementById('helpBackBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.showHelpMenu());
        }
    }

    showHelpMenu() {
        const helpContent = document.querySelector('.help-content');
        const detailPanel = document.getElementById('helpDetailPanel');
        if (helpContent) helpContent.classList.remove('hidden');
        if (detailPanel) detailPanel.classList.add('hidden');
        this.currentView = 'menu';
    }

    showHelpDetail(type) {
        const helpContent = document.querySelector('.help-content');
        const detailPanel = document.getElementById('helpDetailPanel');
        const detailContent = document.getElementById('helpDetailContent');
        
        if (helpContent) helpContent.classList.add('hidden');
        if (detailPanel) detailPanel.classList.remove('hidden');
        
        switch(type) {
            case 'games':
                detailContent.innerHTML = this.getGamesTutorialContent();
                break;
            case 'report':
                detailContent.innerHTML = this.getReportPlayerContent();
                break;
            case 'bug':
                detailContent.innerHTML = this.getBugReportContent();
                break;
            case 'support':
                detailContent.innerHTML = this.getSupportContent();
                break;
        }
        
        this.initFormHandlers(type);
        this.currentView = type;
    }

    getGamesTutorialContent() {
        return `
            <h2>🎮 Games Tutorials</h2>
            <div class="tutorial-section">
                <h3>SI3LN - Space Invaders III Last Night</h3>
                <h4>📖 How to Play</h4>
                <p>SI3LN is a modern take on the classic Space Invaders arcade game.</p>
                <h4>🎮 Controls</h4>
                <ul>
                    <li><strong>Arrow Keys</strong> or <strong>WASD</strong> - Move your ship left/right</li>
                    <li><strong>Space Bar</strong> - Shoot</li>
                    <li><strong>P</strong> - Pause game</li>
                    <li><strong>ESC</strong> - Exit to menu</li>
                </ul>
                <h4>🎯 Gameplay</h4>
                <ul>
                    <li>Destroy all alien invaders before they reach the bottom</li>
                    <li>Use barriers for cover, but they degrade over time</li>
                    <li>Watch out for the UFO - it gives bonus points!</li>
                    <li>Complete levels to unlock new worlds</li>
                </ul>
                <h4>🏆 Scoring</h4>
                <ul>
                    <li>Small aliens: 10 points</li>
                    <li>Medium aliens: 20 points</li>
                    <li>Large aliens: 30 points</li>
                    <li>UFO: 50-300 points (random)</li>
                    <li>Level completion bonus: 1000 points</li>
                </ul>
                <h4>💡 Tips & Tricks</h4>
                <ul>
                    <li>Take your time - accuracy is more important than speed</li>
                    <li>Use barriers strategically</li>
                    <li>Watch the alien movement patterns</li>
                    <li>Save power-ups for later levels</li>
                    <li>Register an account to save your high scores!</li>
                </ul>
            </div>
        `;
    }

    getReportPlayerContent() {
        return `
            <h2>⚠️ Report Player</h2>
            <p>Help us maintain a safe and respectful community. Fill in the form and 
               <strong>download</strong> the report file to send it to our moderation team.</p>
            
            <form class="help-form" id="reportPlayerForm">
                <div class="help-form-group">
                    <label for="reportedUsername">Player Username *</label>
                    <input type="text" id="reportedUsername" class="help-form-input" 
                           placeholder="Enter the username to report" required>
                </div>
                
                <div class="help-form-group">
                    <label for="reportReason">Reason for Report *</label>
                    <select id="reportReason" class="help-form-select" required>
                        <option value="">Select a reason</option>
                        <option value="offensive_username">Offensive Username</option>
                        <option value="offensive_description">Offensive Profile Description</option>
                        <option value="harassment">Harassment</option>
                        <option value="cheating">Cheating/Hacking</option>
                        <option value="spam">Spam</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div class="help-form-group">
                    <label for="reportDetails">Details *</label>
                    <textarea id="reportDetails" class="help-form-textarea" 
                              placeholder="Please provide details about the incident..." required></textarea>
                </div>
                
                <div class="help-form-group">
                    <label for="reportEvidence">Evidence (Optional)</label>
                    <textarea id="reportEvidence" class="help-form-textarea" 
                              placeholder="Describe any evidence (screenshots taken, date/time, etc.)"></textarea>
                </div>
                
                <button type="submit" class="help-form-submit">
                    📥 Download Report File
                </button>
            </form>
            
            <p class="report-note">
                <strong>Note:</strong> The report will be downloaded as a <code>.txt</code> file. 
                You can email it to <strong>support@arcad3x.com</strong> or upload it via the admin panel.
                False reports may result in action against your account.
            </p>
        `;
    }

    getBugReportContent() {
        return `
            <h2>🐛 Report a Bug</h2>
            <p>Found a bug? Fill in the form and <strong>download</strong> the bug report file.</p>
            
            <form class="help-form" id="bugReportForm">
                <div class="help-form-group">
                    <label for="bugTitle">Bug Title *</label>
                    <input type="text" id="bugTitle" class="help-form-input" 
                           placeholder="Brief description of the bug" required>
                </div>
                
                <div class="help-form-group">
                    <label for="bugCategory">Category *</label>
                    <select id="bugCategory" class="help-form-select" required>
                        <option value="">Select category</option>
                        <option value="gameplay">Gameplay</option>
                        <option value="ui">User Interface</option>
                        <option value="login">Login/Authentication</option>
                        <option value="profile">Profile</option>
                        <option value="graphics">Graphics/Visual</option>
                        <option value="audio">Audio</option>
                        <option value="performance">Performance</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div class="help-form-group">
                    <label for="bugDescription">Description *</label>
                    <textarea id="bugDescription" class="help-form-textarea" 
                              placeholder="What happened? What did you expect to happen?" required></textarea>
                </div>
                
                <div class="help-form-group">
                    <label for="bugSteps">Steps to Reproduce</label>
                    <textarea id="bugSteps" class="help-form-textarea" 
                              placeholder="1. Go to...\n2. Click on...\n3. See error"></textarea>
                </div>
                
                <div class="help-form-group">
                    <label for="bugBrowser">Browser & OS</label>
                    <input type="text" id="bugBrowser" class="help-form-input" 
                           placeholder="e.g., Chrome 120 on Windows 11"
                           value="">
                </div>
                
                <button type="submit" class="help-form-submit">
                    📥 Download Bug Report
                </button>
            </form>
        `;
    }

    getSupportContent() {
        return `
            <h2>💝 Support ARCAD3X</h2>
            <div class="support-content-wrapper">
                <div class="support-icon">🎮</div>
                <h3>Thank You for Your Support!</h3>
                <p class="support-description">
                    ARCAD3X is a passion project brought to life by dedicated developers. 
                    Your support helps us continue improving the platform and creating more amazing games.
                </p>
                <div class="support-ways">
                    <h4>Ways to Support Us</h4>
                    <ul class="support-list">
                        <li>⭐ Play our games and share with friends</li>
                        <li>💬 Provide feedback and report bugs</li>
                        <li>📢 Follow us on social media</li>
                        <li>💰 Financial support (Coming Soon)</li>
                    </ul>
                </div>
                <div class="support-payment-notice">
                    <p><strong>💳 Payment options (PayPal, Stripe) coming soon!</strong></p>
                    <p class="payment-hint">We're working on integrating secure payment methods to accept donations.</p>
                </div>
                <p class="support-footer">
                    Created with ❤️ by Hugex & Schps<br>
                    © 2026 ARCAD3X - All rights reserved
                </p>
            </div>
        `;
    }

    initFormHandlers(type) {
        if (type === 'report') {
            const form = document.getElementById('reportPlayerForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this._downloadReportFile(form);
                });
            }
        } else if (type === 'bug') {
            const form = document.getElementById('bugReportForm');
            if (form) {
                // Auto-fill browser info
                const browserInput = document.getElementById('bugBrowser');
                if (browserInput && !browserInput.value) {
                    browserInput.value = this._detectBrowserInfo();
                }
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this._downloadBugReportFile(form);
                });
            }
        }
    }

    /**
     * Generate and download a player report as a .txt file
     */
    _downloadReportFile(form) {
        const data = {
            username: document.getElementById('reportedUsername').value,
            reason: document.getElementById('reportReason').value,
            details: document.getElementById('reportDetails').value,
            evidence: document.getElementById('reportEvidence')?.value || 'N/A',
        };

        if (!data.username || !data.reason || !data.details) {
            alert('Please fill in all required fields.');
            return;
        }

        const reporterName = window.facade?.getLocalUsername()
            || window.api?.getLocalUsername()
            || 'Anonymous';

        const timestamp = new Date().toISOString();
        const version = window.APP_CONFIG?.VERSION || '1.0.0';

        const content = [
            '═══════════════════════════════════════════',
            '        ARCAD3X — PLAYER REPORT',
            '═══════════════════════════════════════════',
            '',
            `Date:            ${timestamp}`,
            `Platform Version: ${version}`,
            `Reporter:        ${reporterName}`,
            '',
            '───────────────────────────────────────────',
            '  REPORTED PLAYER',
            '───────────────────────────────────────────',
            `Username:        ${data.username}`,
            `Reason:          ${data.reason.replace(/_/g, ' ')}`,
            '',
            '───────────────────────────────────────────',
            '  DETAILS',
            '───────────────────────────────────────────',
            data.details,
            '',
            '───────────────────────────────────────────',
            '  EVIDENCE',
            '───────────────────────────────────────────',
            data.evidence,
            '',
            '═══════════════════════════════════════════',
            'Send this file to: support@arcad3x.com',
            '═══════════════════════════════════════════',
        ].join('\n');

        this._triggerDownload(
            content,
            `report-${data.username}-${Date.now()}.txt`,
            'text/plain'
        );

        alert('Report file downloaded! Please email it to support@arcad3x.com');
        this.showHelpMenu();
    }

    /**
     * Generate and download a bug report as a .txt file
     */
    _downloadBugReportFile(form) {
        const data = {
            title: document.getElementById('bugTitle').value,
            category: document.getElementById('bugCategory').value,
            description: document.getElementById('bugDescription').value,
            steps: document.getElementById('bugSteps')?.value || 'N/A',
            browser: document.getElementById('bugBrowser')?.value || 'Unknown',
        };

        if (!data.title || !data.category || !data.description) {
            alert('Please fill in all required fields.');
            return;
        }

        const reporterName = window.facade?.getLocalUsername()
            || window.api?.getLocalUsername()
            || 'Anonymous';

        const timestamp = new Date().toISOString();
        const version = window.APP_CONFIG?.VERSION || '1.0.0';

        const content = [
            '═══════════════════════════════════════════',
            '        ARCAD3X — BUG REPORT',
            '═══════════════════════════════════════════',
            '',
            `Date:            ${timestamp}`,
            `Platform Version: ${version}`,
            `Reporter:        ${reporterName}`,
            `Browser/OS:      ${data.browser}`,
            '',
            '───────────────────────────────────────────',
            '  BUG DETAILS',
            '───────────────────────────────────────────',
            `Title:           ${data.title}`,
            `Category:        ${data.category}`,
            '',
            '───────────────────────────────────────────',
            '  DESCRIPTION',
            '───────────────────────────────────────────',
            data.description,
            '',
            '───────────────────────────────────────────',
            '  STEPS TO REPRODUCE',
            '───────────────────────────────────────────',
            data.steps,
            '',
            '═══════════════════════════════════════════',
            'Send this file to: support@arcad3x.com',
            '═══════════════════════════════════════════',
        ].join('\n');

        this._triggerDownload(
            content,
            `bug-report-${Date.now()}.txt`,
            'text/plain'
        );

        alert('Bug report downloaded! Thank you for helping us improve ARCAD3X.');
        this.showHelpMenu();
    }

    /**
     * Cross-browser file download trigger
     */
    _triggerDownload(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    }

    /**
     * Detect browser and OS info for bug reports
     */
    _detectBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown Browser';
        let os = 'Unknown OS';

        // Detect browser
        if (ua.includes('Firefox/')) browser = 'Firefox ' + ua.split('Firefox/')[1].split(' ')[0];
        else if (ua.includes('Edg/')) browser = 'Edge ' + ua.split('Edg/')[1].split(' ')[0];
        else if (ua.includes('Chrome/')) browser = 'Chrome ' + ua.split('Chrome/')[1].split(' ')[0];
        else if (ua.includes('Safari/') && !ua.includes('Chrome')) browser = 'Safari ' + ua.split('Version/')[1]?.split(' ')[0] || '';
        else if (ua.includes('MSIE') || ua.includes('Trident/')) browser = 'Internet Explorer';

        // Detect OS
        if (ua.includes('Windows NT 10')) os = 'Windows 10/11';
        else if (ua.includes('Windows')) os = 'Windows';
        else if (ua.includes('Mac OS X')) os = 'macOS ' + ua.split('Mac OS X ')[1]?.split(')')[0]?.replace(/_/g, '.') || '';
        else if (ua.includes('Linux')) os = 'Linux';
        else if (ua.includes('Android')) os = 'Android';
        else if (ua.includes('iOS') || ua.includes('iPhone')) os = 'iOS';

        return `${browser} on ${os}`;
    }
}

window.HelpManager = HelpManager;
