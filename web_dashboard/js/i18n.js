// i18n.js - Internationalization manager
class I18nManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.translations = {};
        this.loadTranslations();
    }

    loadTranslations() {
        this.translations = {
            en: {
                // Navigation & Menu
                menu: {
                    home: "Home",
                    profile: "Profile",
                    games: "Games",
                    help: "Help",
                    settings: "Settings",
                    aboutUs: "About us",
                    logout: "Logout"
                },
                // Top bar
                topBar: {
                    search: "Search...",
                    loginSignup: "🔐 Login / Sign Up",
                    logout: "Logout"
                },
                // Home page
                home: {
                    welcome: "Welcome in",
                    subtitle: "Fullstack gaming platform",
                    launchAdventure: "Launch the adventure",
                    playNow: "Play now →",
                    leaderboard: "Leaderboard",
                    playerProfile: "Player Profile",
                    loading: "Loading..."
                },
                // Login page
                login: {
                    title: "🔐 Login to ARCAD3X",
                    username: "Username",
                    password: "Password",
                    usernamePlaceholder: "Your username",
                    passwordPlaceholder: "********",
                    rememberMe: "Remember me",
                    loginButton: "Login",
                    forgotPassword: "Forgot password?",
                    createAccount: "Create an account"
                },
                // Signup page
                signup: {
                    title: "📝 Create an account",
                    email: "Email",
                    emailPlaceholder: "your@email.com",
                    pseudo: "Pseudo",
                    pseudoPlaceholder: "Choose your username",
                    pseudoWarning: "⚠️ This username cannot be changed later (only admins can modify it)",
                    password: "Password",
                    confirmPassword: "Confirm password",
                    passwordPlaceholder: "********",
                    reqLength: "✗ 8 characters min",
                    reqNumber: "✗ At least 1 number",
                    reqUpper: "✗ At least 1 uppercase",
                    preferredLanguage: "Preferred Language",
                    acceptTerms: "I accept the",
                    termsOfService: "terms of service",
                    createButton: "Create my account",
                    alreadyHaveAccount: "Already have an account?",
                    loginLink: "Login here"
                },
                // Profile page
                profile: {
                    editProfile: "Edit Profile",
                    backgroundColor: "🎨 Background Color",
                    profilePicture: "📸 Profile Picture (max 5MB)",
                    chooseImage: "Choose Image",
                    imageHint: "PNG, JPG, GIF up to 5MB",
                    bio: "📝 Bio",
                    bioPlaceholder: "Tell us about yourself...",
                    privacy: "🔒 Privacy",
                    showScores: "Show my scores on profile",
                    favoriteGames: "⭐ Favorite Games",
                    multiSelectHint: "Hold Ctrl/Cmd to select multiple",
                    saveChanges: "Save Changes",
                    cancel: "Cancel"
                },
                // Games page
                games: {
                    title: "Games",
                    comingSoon: "Coming Soon",
                    guestWarning: "⚠️ You're playing as a guest. Your progress will not be saved.",
                    loginToSave: "Login",
                    registerToSave: "Register",
                    toSaveProgress: "to save your progress",
                    fullscreen: "Fullscreen",
                    exitFullscreen: "Exit Fullscreen",
                    previousGame: "◀ Previous",
                    nextGame: "Next ▶"
                },
                // Help page
                help: {
                    title: "Help Center",
                    tutorials: "Game Tutorials",
                    tutorialsDesc: "Learn how to play our games",
                    viewTutorials: "View Tutorials",
                    reportPlayer: "Report Player",
                    reportPlayerDesc: "Report inappropriate behavior",
                    reportPlayerBtn: "Report a Player",
                    reportBug: "Report Bug",
                    reportBugDesc: "Help us improve by reporting issues",
                    reportBugBtn: "Report a Bug",
                    support: "Support Us",
                    supportDesc: "Support the development of ARCAD3X",
                    supportBtn: "Support Project",
                    backToMenu: "← Back to Help Menu"
                },
                // Settings page
                settings: {
                    title: "⚙️ Settings",
                    language: "Language",
                    changeLanguage: "Change language"
                },
                // About page
                about: {
                    title: "ℹ️ About us"
                },
                // Common
                common: {
                    close: "Close",
                    save: "Save",
                    cancel: "Cancel",
                    submit: "Submit",
                    back: "Back",
                    next: "Next",
                    previous: "Previous",
                    loading: "Loading...",
                    error: "Error",
                    success: "Success"
                }
            },
            fr: {
                // Navigation & Menu
                menu: {
                    home: "Accueil",
                    profile: "Profil",
                    games: "Jeux",
                    help: "Aide",
                    settings: "Paramètres",
                    aboutUs: "À propos",
                    logout: "Déconnexion"
                },
                // Top bar
                topBar: {
                    search: "Rechercher...",
                    loginSignup: "🔐 Connexion / Inscription",
                    logout: "Déconnexion"
                },
                // Home page
                home: {
                    welcome: "Bienvenue dans",
                    subtitle: "Plateforme de jeu fullstack",
                    launchAdventure: "Lancez l'aventure",
                    playNow: "Jouer maintenant →",
                    leaderboard: "Classement",
                    playerProfile: "Profil Joueur",
                    loading: "Chargement..."
                },
                // Login page
                login: {
                    title: "🔐 Connexion à ARCAD3X",
                    username: "Nom d'utilisateur",
                    password: "Mot de passe",
                    usernamePlaceholder: "Votre nom d'utilisateur",
                    passwordPlaceholder: "********",
                    rememberMe: "Se souvenir de moi",
                    loginButton: "Se connecter",
                    forgotPassword: "Mot de passe oublié ?",
                    createAccount: "Créer un compte"
                },
                // Signup page
                signup: {
                    title: "📝 Créer un compte",
                    email: "Email",
                    emailPlaceholder: "votre@email.com",
                    pseudo: "Pseudo",
                    pseudoPlaceholder: "Choisissez votre nom d'utilisateur",
                    pseudoWarning: "⚠️ Ce pseudo ne pourra pas être changé plus tard (seuls les administrateurs pourront le modifier)",
                    password: "Mot de passe",
                    confirmPassword: "Confirmer le mot de passe",
                    passwordPlaceholder: "********",
                    reqLength: "✗ 8 caractères min",
                    reqNumber: "✗ Au moins 1 chiffre",
                    reqUpper: "✗ Au moins 1 majuscule",
                    preferredLanguage: "Langue préférée",
                    acceptTerms: "J'accepte les",
                    termsOfService: "conditions d'utilisation",
                    createButton: "Créer mon compte",
                    alreadyHaveAccount: "Déjà un compte ?",
                    loginLink: "Connectez-vous"
                },
                // Profile page
                profile: {
                    editProfile: "Modifier le profil",
                    backgroundColor: "🎨 Couleur de fond",
                    profilePicture: "📸 Photo de profil (max 5MB)",
                    chooseImage: "Choisir une image",
                    imageHint: "PNG, JPG, GIF jusqu'à 5MB",
                    bio: "📝 Biographie",
                    bioPlaceholder: "Parlez-nous de vous...",
                    privacy: "🔒 Confidentialité",
                    showScores: "Afficher mes scores sur mon profil",
                    favoriteGames: "⭐ Jeux favoris",
                    multiSelectHint: "Maintenez Ctrl/Cmd pour sélectionner plusieurs",
                    saveChanges: "Enregistrer les modifications",
                    cancel: "Annuler"
                },
                // Games page
                games: {
                    title: "Jeux",
                    comingSoon: "Bientôt disponible",
                    guestWarning: "⚠️ Vous jouez en tant qu'invité. Votre progression ne sera pas sauvegardée.",
                    loginToSave: "Connexion",
                    registerToSave: "Inscription",
                    toSaveProgress: "pour sauvegarder votre progression",
                    fullscreen: "Plein écran",
                    exitFullscreen: "Quitter le plein écran",
                    previousGame: "◀ Précédent",
                    nextGame: "Suivant ▶"
                },
                // Help page
                help: {
                    title: "Centre d'aide",
                    tutorials: "Tutoriels de jeu",
                    tutorialsDesc: "Apprenez à jouer à nos jeux",
                    viewTutorials: "Voir les tutoriels",
                    reportPlayer: "Signaler un joueur",
                    reportPlayerDesc: "Signaler un comportement inapproprié",
                    reportPlayerBtn: "Signaler un joueur",
                    reportBug: "Signaler un bug",
                    reportBugDesc: "Aidez-nous à nous améliorer en signalant des problèmes",
                    reportBugBtn: "Signaler un bug",
                    support: "Nous soutenir",
                    supportDesc: "Soutenez le développement d'ARCAD3X",
                    supportBtn: "Soutenir le projet",
                    backToMenu: "← Retour au menu d'aide"
                },
                // Settings page
                settings: {
                    title: "⚙️ Paramètres",
                    language: "Langue",
                    changeLanguage: "Changer de langue"
                },
                // About page
                about: {
                    title: "ℹ️ À propos de nous"
                },
                // Common
                common: {
                    close: "Fermer",
                    save: "Enregistrer",
                    cancel: "Annuler",
                    submit: "Soumettre",
                    back: "Retour",
                    next: "Suivant",
                    previous: "Précédent",
                    loading: "Chargement...",
                    error: "Erreur",
                    success: "Succès"
                }
            }
        };
    }

    // Get translation by key path (e.g., "menu.home")
    t(key) {
        const keys = key.split('.');
        let value = this.translations[this.currentLanguage];
        
        for (const k of keys) {
            value = value?.[k];
            if (value === undefined) {
                console.warn(`Translation not found for key: ${key}`);
                return key;
            }
        }
        
        return value;
    }

    // Set language and update UI
    setLanguage(lang) {
        if (!this.translations[lang]) {
            console.error(`Language ${lang} not supported`);
            return;
        }
        
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.updateUI();
        
        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
    }

    // Get current language
    getLanguage() {
        return this.currentLanguage;
    }

    // Update all UI elements with data-i18n attribute
    updateUI() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            // Check if element has data-i18n-attr (for placeholders, titles, etc.)
            const attr = element.getAttribute('data-i18n-attr');
            if (attr) {
                element.setAttribute(attr, translation);
            } else {
                // Update text content
                element.textContent = translation;
            }
        });
        
        // Update placeholders separately
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
    }

    // Initialize i18n on page load
    init() {
        // Update UI with current language
        this.updateUI();
        
        // Listen for language changes from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'language' && e.newValue) {
                this.currentLanguage = e.newValue;
                this.updateUI();
            }
        });
    }

    // Get available languages
    getAvailableLanguages() {
        return [
            { code: 'en', name: 'English', flag: '🇬🇧' },
            { code: 'fr', name: 'Français', flag: '🇫🇷' }
        ];
    }
}

// Global instance
window.i18n = new I18nManager();
