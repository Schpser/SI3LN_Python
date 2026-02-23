// help.js - Help page management module
class HelpManager {
    constructor() {
        this.currentView = 'menu';
    }

    initHelpHandlers() {
        // Help button handlers
        const helpButtons = document.querySelectorAll('.help-btn');
        helpButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const helpType = e.target.getAttribute('data-help');
                this.showHelpDetail(helpType);
            });
        });

        // Back button handler
        const backBtn = document.getElementById('helpBackBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.showHelpMenu();
            });
        }
    }

    showHelpMenu() {
        document.querySelector('.help-content').classList.remove('hidden');
        document.getElementById('helpDetailPanel').classList.add('hidden');
        this.currentView = 'menu';
    }

    showHelpDetail(type) {
        document.querySelector('.help-content').classList.add('hidden');
        const detailPanel = document.getElementById('helpDetailPanel');
        const detailContent = document.getElementById('helpDetailContent');
        
        detailPanel.classList.remove('hidden');
        
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
        
        // Initialize form handlers if applicable
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
            <p>Help us maintain a safe and respectful community. Use this form to report offensive behavior.</p>
            
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
                    <input type="text" id="reportEvidence" class="help-form-input" 
                           placeholder="Link to screenshot or other evidence">
                </div>
                
                <button type="submit" class="help-form-submit">Submit Report</button>
            </form>
            
            <p style="margin-top: 30px; color: #888; font-size: 0.9rem;">
                <strong>Note:</strong> False reports may result in action against your account. 
                All reports are reviewed by our moderation team.
            </p>
        `;
    }

    getBugReportContent() {
        return `
            <h2>🐛 Report a Bug</h2>
            <p>Found a bug? Help us improve ARCAD3X by reporting it here.</p>
            
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
                              placeholder="1. Go to...&#10;2. Click on...&#10;3. See error"></textarea>
                </div>
                
                <div class="help-form-group">
                    <label for="bugBrowser">Browser & OS</label>
                    <input type="text" id="bugBrowser" class="help-form-input" 
                           placeholder="e.g., Chrome 120 on Windows 11">
                </div>
                
                <button type="submit" class="help-form-submit">Submit Bug Report</button>
            </form>
        `;
    }

    getSupportContent() {
        return `
            <h2>💝 Support ARCAD3X</h2>
            
            <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">🎮</div>
                <h3 style="margin-bottom: 20px; color: #ffffff;">Thank You for Your Support!</h3>
                <p style="font-size: 1.1rem; margin-bottom: 30px; color: #cccccc; line-height: 1.8;">
                    ARCAD3X is a passion project brought to life by dedicated developers. 
                    Your support helps us continue improving the platform and creating more amazing games.
                </p>
                
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.2); 
                            border-radius: 15px; padding: 30px; margin: 30px 0;">
                    <h4 style="margin-bottom: 15px; color: #ffffff;">Ways to Support Us</h4>
                    <ul style="list-style: none; padding: 0; text-align: left; max-width: 500px; margin: 0 auto;">
                        <li style="margin: 15px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                            ⭐ Play our games and share with friends
                        </li>
                        <li style="margin: 15px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                            💬 Provide feedback and report bugs
                        </li>
                        <li style="margin: 15px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                            📢 Follow us on social media
                        </li>
                        <li style="margin: 15px 0; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                            💰 Financial support (Coming Soon)
                        </li>
                    </ul>
                </div>
                
                <div style="margin-top: 40px; padding: 20px; background: rgba(255, 165, 0, 0.1); 
                            border: 1px solid rgba(255, 165, 0, 0.3); border-radius: 10px;">
                    <p style="font-size: 1rem; color: #ffa500; margin: 0;">
                        <strong>💳 Payment options (PayPal, Stripe) coming soon!</strong><br>
                        <span style="font-size: 0.9rem; color: #888;">
                            We're working on integrating secure payment methods to accept donations.
                        </span>
                    </p>
                </div>
                
                <p style="margin-top: 30px; font-size: 0.9rem; color: #888;">
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
                    this.handleReportSubmit(form);
                });
            }
        } else if (type === 'bug') {
            const form = document.getElementById('bugReportForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleBugSubmit(form);
                });
            }
        }
    }

    async handleReportSubmit(form) {
        const data = {
            username: document.getElementById('reportedUsername').value,
            reason: document.getElementById('reportReason').value,
            details: document.getElementById('reportDetails').value,
            evidence: document.getElementById('reportEvidence').value
        };

        try {
            // TODO: Implement API call when backend is ready
            console.log('Report submitted:', data);
            alert('Thank you for your report. Our moderation team will review it shortly.');
            this.showHelpMenu();
        } catch (error) {
            console.error('Error submitting report:', error);
            alert('Error submitting report. Please try again later.');
        }
    }

    async handleBugSubmit(form) {
        const data = {
            title: document.getElementById('bugTitle').value,
            category: document.getElementById('bugCategory').value,
            description: document.getElementById('bugDescription').value,
            steps: document.getElementById('bugSteps').value,
            browser: document.getElementById('bugBrowser').value
        };

        try {
            // TODO: Implement API call when backend is ready
            console.log('Bug report submitted:', data);
            alert('Thank you for reporting this bug! We\'ll investigate it as soon as possible.');
            this.showHelpMenu();
        } catch (error) {
            console.error('Error submitting bug report:', error);
            alert('Error submitting bug report. Please try again later.');
        }
    }
}

// Export for use in main app
window.HelpManager = HelpManager;
