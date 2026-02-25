// auth.js - Authentication management module
class AuthManager {
    constructor(apiClient) {
        this.api = apiClient;
    }

    initLoginPage() {
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLogin();
        });

        // Handle "Create an account" link on login page
        const signupLink = document.getElementById('signupLink');
        if (signupLink) {
            signupLink.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.app) {
                    window.app.navigateTo('create-account');
                }
            });
        }

        // Handle "Forgot password" link
        const forgotLink = document.getElementById('forgotPasswordLink');
        if (forgotLink) {
            forgotLink.addEventListener('click', (e) => {
                e.preventDefault();
                alert('Password recovery feature coming soon!');
            });
        }
    }

    async handleSignup() {
        if (!this.validateForm()) {
            alert('Please fix the form errors before submitting.');
            return;
        }
        const username = document.getElementById('signupPseudo')?.value;
        const email    = document.getElementById('signupEmail')?.value;
        const password = document.getElementById('signupPassword')?.value;

        const submitBtn = document.getElementById('signupSubmit');
        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Creating…'; }

        try {
            const result = await this.api.signup({ username, email, password });
            localStorage.setItem('access_token', result.token);
            if (window.app) {
                window.app.navigateTo('home');
                window.app.checkAuth();
                window.app.loadHomeData();
            }
        } catch (err) {
            console.error('Signup error:', err);
            alert('Registration failed. Username or email may already be taken.');
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Create my account'; }
        }
    }

    async handleLogin() {
        const username = document.getElementById('loginUsername')?.value;
        const password = document.getElementById('loginPassword')?.value;

        if (!username || !password) {
            alert('Please fill in all fields');
            return;
        }

        try {
            const submitBtn = document.getElementById('loginSubmitBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Logging in...';
            }

            await this.login(username, password);
            
            // Redirect to home
            if (window.app) {
                window.app.navigateTo('home');
                window.app.checkAuth();
            }
            
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed. Please check your credentials.');
            
            const submitBtn = document.getElementById('loginSubmitBtn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Login';
            }
        }
    }

    async login(username, password) {
        try {
            const result = await this.api.login(username, password);
            localStorage.setItem('access_token', result.token);
            return true;
        } catch (error) {
            console.error('Error logging in:', error);
            throw error;
        }
    }

    logout() {
        localStorage.removeItem('access_token');
        this.applyRoleUI('guest');
    }

    /** Return the current role decoded from the JWT: 'admin' | 'player' | 'guest' */
    getRole() {
        return window.api ? window.api.getLocalRole() : 'guest';
    }

    /**
     * Show/hide elements based on role.
     * HTML markup conventions used across index.html:
     *   .admin-only   → visible only to admin/staff
     *   .player-only  → visible to authenticated players (+ admin)
     *   .guest-only   → visible only when NOT logged in
     *   .auth-required → hidden for guests (alias of .player-only)
     */
    applyRoleUI(role) {
        const isGuest  = role === 'guest';
        const isPlayer = role === 'player' || role === 'admin';
        const isAdmin  = role === 'admin';

        // admin-only sections (e.g. Settings menu item)
        document.querySelectorAll('.admin-only').forEach(el => {
            el.classList.toggle('hidden', !isAdmin);
        });

        // player-only / auth-required sections
        document.querySelectorAll('.player-only, .auth-required').forEach(el => {
            el.classList.toggle('hidden', !isPlayer);
        });

        // guest-only sections (login banner, guest hint, etc.)
        document.querySelectorAll('.guest-only').forEach(el => {
            el.classList.toggle('hidden', isPlayer);
        });

        // Profile menu item: hide for guests
        const profileItem = document.querySelector('.menu-item[data-page="profile"]');
        if (profileItem) {
            profileItem.classList.toggle('hidden', isGuest);
        }
    }

    checkAuth() {
        const token = localStorage.getItem('access_token');
        return !!token;
    }

    updateAuthUI(isLoggedIn, username = '') {
        const topBarAuth = document.getElementById('topBarAuth');
        const userInfo   = document.getElementById('userInfo');
        const userName   = document.getElementById('userName');

        if (isLoggedIn) {
            topBarAuth?.classList.add('hidden');
            userInfo?.classList.remove('hidden');
            if (userName) {
                const displayName = username || window.api?.getLocalUsername() || 'Player';
                userName.textContent = displayName;
            }
        } else {
            topBarAuth?.classList.remove('hidden');
            userInfo?.classList.add('hidden');
        }

        // Apply role-based visibility rules
        const role = isLoggedIn ? this.getRole() : 'guest';
        this.applyRoleUI(role);
    }

    initSignupValidation() {
        const form = document.getElementById('signupForm');
        if (!form) return;
        
        const pseudo = document.getElementById('signupPseudo');
        const email = document.getElementById('signupEmail');
        const password = document.getElementById('signupPassword');
        const confirm = document.getElementById('signupConfirmPassword');
        const terms = document.getElementById('acceptTerms');
        const submitBtn = document.getElementById('signupSubmit');
        
        // Validation en temps réel
        pseudo?.addEventListener('input', () => this.validatePseudo(pseudo));
        email?.addEventListener('input', () => this.validateEmail(email));
        password?.addEventListener('input', () => this.validatePassword(password));
        confirm?.addEventListener('input',() => this.matchPasswords(password, confirm));
        
        // Vérification globale pour activer le bouton
        [pseudo, email, password, confirm, terms].forEach(field => {
            field?.addEventListener('input', () => {
                if (submitBtn) {
                    submitBtn.disabled = !this.validateForm();
                }
            });
        });
        
        terms?.addEventListener('change', () => {
            if (submitBtn) {
                submitBtn.disabled = !this.validateForm();
            }
        });
        
        // Soumission du formulaire
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSignup();
        });
    }

    validatePseudo(input) {
        const value = input.value;
        const validation = document.getElementById('pseudoValidation');
        
        // Vérifier les gros mots (simulé)
        const profanityList = ['badword1', 'badword2'];
        const hasProfanity = profanityList.some(word => value.toLowerCase().includes(word));
        
        if (hasProfanity) {
            input.classList.add('invalid');
            input.classList.remove('valid');
            if (validation) {
                validation.innerHTML = '❌ Ce pseudo contient des termes inappropriés';
                validation.style.color = '#ff4444';
            }
            return false;
        }
        
        // Vérifier format
        const isValid = /^[A-Za-z0-9_]+$/.test(value) && value.length >= 3;
        
        if (isValid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
            if (validation) {
                validation.innerHTML = '✓ Pseudo disponible';
                validation.style.color = '#44ff44';
            }
        } else {
            input.classList.add('invalid');
            input.classList.remove('valid');
            if (validation) {
                validation.innerHTML = '❌ 3 caractères minimum, uniquement lettres, chiffres et _';
                validation.style.color = '#ff4444';
            }
        }
        
        return isValid;
    }

    validateEmail(input) {
        const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value);
        
        if (isValid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
        } else {
            input.classList.add('invalid');
            input.classList.remove('valid');
        }
        
        return isValid;
    }

    validatePassword(input) {
        const value = input.value;
        
        const checks = {
            length: value.length >= 8,
            number: /\d/.test(value),
            upper: /[A-Z]/.test(value)
        };
        
        // Mettre à jour les indicateurs
        const reqLength = document.getElementById('reqLength');
        const reqNumber = document.getElementById('reqNumber');
        const reqUpper = document.getElementById('reqUpper');
        
        if (reqLength) reqLength.className = checks.length ? 'req-item valid' : 'req-item invalid';
        if (reqNumber) reqNumber.className = checks.number ? 'req-item valid' : 'req-item invalid';
        if (reqUpper) reqUpper.className = checks.upper ? 'req-item valid' : 'req-item invalid';
        
        const isValid = checks.length && checks.number && checks.upper;
        
        if (isValid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
        } else {
            input.classList.add('invalid');
            input.classList.remove('valid');
        }
        
        return isValid;
    }

    matchPasswords(password, confirm) {
        const match = password.value === confirm.value;
        const message = document.getElementById('passwordMatch');
        
        if (match) {
            confirm.classList.add('valid');
            confirm.classList.remove('invalid');
            if (message) {
                message.innerHTML = '✓ Les mots de passe correspondent';
                message.style.color = '#44ff44';
            }
        } else {
            confirm.classList.add('invalid');
            confirm.classList.remove('valid');
            if (message) {
                message.innerHTML = '❌ Les mots de passe ne correspondent pas';
                message.style.color = '#ff4444';
            }
        }
        
        return match;
    }

    validateForm() {
        const pseudo = document.getElementById('signupPseudo');
        const email = document.getElementById('signupEmail');
        const password = document.getElementById('signupPassword');
        const confirm = document.getElementById('signupConfirmPassword');
        const terms = document.getElementById('acceptTerms');
        
        return this.validatePseudo(pseudo) &&
            this.validateEmail(email) &&
            this.validatePassword(password) &&
            this.matchPasswords(password, confirm) &&
            terms?.checked;
    }

}


// Export for use in main app
window.AuthManager = AuthManager;
