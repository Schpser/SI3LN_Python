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

        // Re-render current detail view on language change
        window.addEventListener('languageChanged', () => {
            if (this.currentView !== 'menu') {
                this.showHelpDetail(this.currentView);
            }
        });
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
        const t = (k) => window.i18n.t(k);
        return `
            <h2>${t('help.gamesPageTitle')}</h2>
            <div class="tutorial-section">
                <h3>${t('help.si3lnTitle')}</h3>
                <h4>${t('help.howToPlay')}</h4>
                <p>${t('help.si3lnDesc')}</p>
                <h4>${t('help.controlsTitle')}</h4>
                <ul>
                    <li>${t('help.ctrlMove')}</li>
                    <li>${t('help.ctrlShoot')}</li>
                    <li>${t('help.ctrlPause')}</li>
                    <li>${t('help.ctrlExit')}</li>
                </ul>
                <h4>${t('help.gameplayTitle')}</h4>
                <ul>
                    <li>${t('help.gameplay1')}</li>
                    <li>${t('help.gameplay2')}</li>
                    <li>${t('help.gameplay3')}</li>
                    <li>${t('help.gameplay4')}</li>
                </ul>
                <h4>${t('help.scoringTitle')}</h4>
                <ul>
                    <li>${t('help.score1')}</li>
                    <li>${t('help.score2')}</li>
                    <li>${t('help.score3')}</li>
                    <li>${t('help.score4')}</li>
                    <li>${t('help.score5')}</li>
                </ul>
                <h4>${t('help.tipsTitle')}</h4>
                <ul>
                    <li>${t('help.tip1')}</li>
                    <li>${t('help.tip2')}</li>
                    <li>${t('help.tip3')}</li>
                    <li>${t('help.tip4')}</li>
                    <li>${t('help.tip5')}</li>
                </ul>
            </div>
        `;
    }

    getReportPlayerContent() {
        const t = (k) => window.i18n.t(k);
        return `
            <h2>${t('help.reportTitle')}</h2>
            <p>${t('help.reportDesc')}</p>

            <form class="help-form" id="reportPlayerForm">
                <div class="help-form-group">
                    <label for="reportedUsername">${t('help.reportUsernameLbl')}</label>
                    <input type="text" id="reportedUsername" class="help-form-input"
                           placeholder="${t('help.reportUsernamePh')}" required>
                </div>

                <div class="help-form-group">
                    <label for="reportReason">${t('help.reportReasonLbl')}</label>
                    <select id="reportReason" class="help-form-select" required>
                        <option value="">${t('help.reportReasonPh')}</option>
                        <option value="offensive_username">${t('help.reportReasonOffUser')}</option>
                        <option value="offensive_description">${t('help.reportReasonOffDesc')}</option>
                        <option value="harassment">${t('help.reportReasonHaras')}</option>
                        <option value="cheating">${t('help.reportReasonCheat')}</option>
                        <option value="spam">${t('help.reportReasonSpam')}</option>
                        <option value="other">${t('help.reportReasonOther')}</option>
                    </select>
                </div>

                <div class="help-form-group">
                    <label for="reportDetails">${t('help.reportDetailsLbl')}</label>
                    <textarea id="reportDetails" class="help-form-textarea"
                              placeholder="${t('help.reportDetailsPh')}" required></textarea>
                </div>

                <div class="help-form-group">
                    <label for="reportEvidence">${t('help.reportEvidenceLbl')}</label>
                    <textarea id="reportEvidence" class="help-form-textarea"
                              placeholder="${t('help.reportEvidencePh')}"></textarea>
                </div>

                <button type="submit" class="help-form-submit">
                    ${t('help.reportSubmitBtn')}
                </button>
            </form>

            <p class="report-note">
                ${t('help.reportNote')}
            </p>
        `;
    }

    getBugReportContent() {
        const t = (k) => window.i18n.t(k);
        return `
            <h2>${t('help.bugPageTitle')}</h2>
            <p>${t('help.bugDesc')}</p>

            <form class="help-form" id="bugReportForm">
                <div class="help-form-group">
                    <label for="bugTitle">${t('help.bugTitleLbl')}</label>
                    <input type="text" id="bugTitle" class="help-form-input"
                           placeholder="${t('help.bugTitlePh')}" required>
                </div>

                <div class="help-form-group">
                    <label for="bugCategory">${t('help.bugCategoryLbl')}</label>
                    <select id="bugCategory" class="help-form-select" required>
                        <option value="">${t('help.bugCategoryPh')}</option>
                        <option value="gameplay">${t('help.bugCatGameplay')}</option>
                        <option value="ui">${t('help.bugCatUI')}</option>
                        <option value="login">${t('help.bugCatLogin')}</option>
                        <option value="profile">${t('help.bugCatProfile')}</option>
                        <option value="graphics">${t('help.bugCatGraphics')}</option>
                        <option value="audio">${t('help.bugCatAudio')}</option>
                        <option value="performance">${t('help.bugCatPerf')}</option>
                        <option value="other">${t('help.bugCatOther')}</option>
                    </select>
                </div>

                <div class="help-form-group">
                    <label for="bugDescription">${t('help.bugDescLbl')}</label>
                    <textarea id="bugDescription" class="help-form-textarea"
                              placeholder="${t('help.bugDescPh')}" required></textarea>
                </div>

                <div class="help-form-group">
                    <label for="bugSteps">${t('help.bugStepsLbl')}</label>
                    <textarea id="bugSteps" class="help-form-textarea"
                              placeholder="${t('help.bugStepsPh')}"></textarea>
                </div>

                <div class="help-form-group">
                    <label for="bugBrowser">${t('help.bugBrowserLbl')}</label>
                    <input type="text" id="bugBrowser" class="help-form-input"
                           placeholder="${t('help.bugBrowserPh')}"
                           value="">
                </div>

                <button type="submit" class="help-form-submit">
                    ${t('help.bugSubmitBtn')}
                </button>
            </form>
        `;
    }

    getSupportContent() {
        const t = (k) => window.i18n.t(k);
        return `
            <h2>${t('help.supportTitle')}</h2>
            <div class="support-content-wrapper">
                <div class="support-icon">🎮</div>
                <h3>${t('help.supportThankYou')}</h3>
                <p class="support-description">
                    ${t('help.supportDesc2')}
                </p>
                <div class="support-ways">
                    <h4>${t('help.supportWaysTitle')}</h4>
                    <ul class="support-list">
                        <li>${t('help.supportWay1')}</li>
                        <li>${t('help.supportWay2')}</li>
                        <li>${t('help.supportWay3')}</li>
                        <li>${t('help.supportWay4')}</li>
                    </ul>
                </div>
                <div class="support-payment-notice">
                    <p><strong>${t('help.supportPaymentTitle')}</strong></p>
                    <p class="payment-hint">${t('help.supportPaymentHint')}</p>
                </div>
                <p class="support-footer">
                    ${t('help.supportFooter')}<br>
                    ${t('about.copyright')}
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
