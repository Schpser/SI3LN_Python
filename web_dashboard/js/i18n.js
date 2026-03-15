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
                    loading: "Loading...",
                    noScores: "No scores yet. Be the first to play!",
                    leaderboardError: "Could not load leaderboard.",
                    welcomeUser: "Welcome,",
                    pleaseLogin: "Please log in"
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
                    loginLink: "Login here",
                    pseudoAvailable: "✓ Username available",
                    pseudoProfanity: "❌ Username contains inappropriate terms",
                    pseudoFormat: "❌ Min. 3 characters, letters, digits and _ only",
                    passwordsMatch: "✓ Passwords match",
                    passwordsNoMatch: "❌ Passwords do not match"
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
                    cancel: "Cancel",
                    noGamesPlayed: "No games played yet!",
                    loginToSeeScores: "Log in to see your scores"
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
                    backToMenu: "← Back to Help Menu",
                    gamesPageTitle: "🎮 Games Tutorials",
                    si3lnTitle: "SI3LN - Space Invaders III Last Night",
                    howToPlay: "📖 How to Play",
                    si3lnDesc: "SI3LN is a modern take on the classic Space Invaders arcade game.",
                    controlsTitle: "🎮 Controls",
                    ctrlMove: "Arrow Keys or WASD — Move your ship left/right",
                    ctrlShoot: "Space Bar — Shoot",
                    ctrlPause: "P — Pause game",
                    ctrlExit: "ESC — Exit to menu",
                    gameplayTitle: "🎯 Gameplay",
                    gameplay1: "Destroy all alien invaders before they reach the bottom",
                    gameplay2: "Use barriers for cover, but they degrade over time",
                    gameplay3: "Watch out for the UFO - it gives bonus points!",
                    gameplay4: "Complete levels to unlock new worlds",
                    scoringTitle: "🏆 Scoring",
                    score1: "Small aliens: 10 points",
                    score2: "Medium aliens: 20 points",
                    score3: "Large aliens: 30 points",
                    score4: "UFO: 50-300 points (random)",
                    score5: "Level completion bonus: 1000 points",
                    tipsTitle: "💡 Tips & Tricks",
                    tip1: "Take your time - accuracy is more important than speed",
                    tip2: "Use barriers strategically",
                    tip3: "Watch the alien movement patterns",
                    tip4: "Save power-ups for later levels",
                    tip5: "Register an account to save your high scores!",
                    reportTitle: "⚠️ Report Player",
                    reportDesc: "Help us maintain a safe and respectful community. Fill in the form and download the report file to send it to our moderation team.",
                    reportUsernameLbl: "Player Username *",
                    reportUsernamePh: "Enter the username to report",
                    reportReasonLbl: "Reason for Report *",
                    reportReasonPh: "Select a reason",
                    reportReasonOffUser: "Offensive Username",
                    reportReasonOffDesc: "Offensive Profile Description",
                    reportReasonHaras: "Harassment",
                    reportReasonCheat: "Cheating/Hacking",
                    reportReasonSpam: "Spam",
                    reportReasonOther: "Other",
                    reportDetailsLbl: "Details *",
                    reportDetailsPh: "Please provide details about the incident...",
                    reportEvidenceLbl: "Evidence (Optional)",
                    reportEvidencePh: "Describe any evidence (screenshots taken, date/time, etc.)",
                    reportSubmitBtn: "📥 Download Report File",
                    reportNote: "Note: The report will be downloaded as a .txt file. You can email it to support@arcad3x.com or upload it via the admin panel. False reports may result in action against your account.",
                    bugPageTitle: "🐛 Report a Bug",
                    bugDesc: "Found a bug? Fill in the form and download the bug report file.",
                    bugTitleLbl: "Bug Title *",
                    bugTitlePh: "Brief description of the bug",
                    bugCategoryLbl: "Category *",
                    bugCategoryPh: "Select category",
                    bugCatGameplay: "Gameplay",
                    bugCatUI: "User Interface",
                    bugCatLogin: "Login/Authentication",
                    bugCatProfile: "Profile",
                    bugCatGraphics: "Graphics/Visual",
                    bugCatAudio: "Audio",
                    bugCatPerf: "Performance",
                    bugCatOther: "Other",
                    bugDescLbl: "Description *",
                    bugDescPh: "What happened? What did you expect to happen?",
                    bugStepsLbl: "Steps to Reproduce",
                    bugStepsPh: "1. Go to...\n2. Click on...\n3. See error",
                    bugBrowserLbl: "Browser & OS",
                    bugBrowserPh: "e.g., Chrome 120 on Windows 11",
                    bugSubmitBtn: "📥 Download Bug Report",
                    supportTitle: "💝 Support ARCAD3X",
                    supportThankYou: "Thank You for Your Support!",
                    supportDesc2: "ARCAD3X is a passion project brought to life by dedicated developers. Your support helps us continue improving the platform and creating more amazing games.",
                    supportWaysTitle: "Ways to Support Us",
                    supportWay1: "⭐ Play our games and share with friends",
                    supportWay2: "💬 Provide feedback and report bugs",
                    supportWay3: "📢 Follow us on social media",
                    supportWay4: "💰 Financial support (Coming Soon)",
                    supportPaymentTitle: "💳 Payment options (PayPal, Stripe) coming soon!",
                    supportPaymentHint: "We're working on integrating secure payment methods to accept donations.",
                    supportFooter: "Created with ❤️ by Hugex & Schps"
                },
                // Search
                search: {
                    noResults: "No results found"
                },
                // Settings page
                settings: {
                    title: "⚙️ Settings",
                    language: "Language",
                    changeLanguage: "Change language"
                },
                // About page
                about: {
                    title: "ℹ️ About us",
                    description: "SI3LN project by Hugex & Schps",
                    platform: "FullStack gaming platform",
                    copyright: "© 2026 ARCAD3X - All rights reserved"
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
                    loading: "Chargement...",
                    noScores: "Aucun score pour l'instant. Soyez le premier à jouer !",
                    leaderboardError: "Impossible de charger le classement.",
                    welcomeUser: "Bienvenue,",
                    pleaseLogin: "Veuillez vous connecter"
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
                    loginLink: "Connectez-vous",
                    pseudoAvailable: "✓ Pseudo disponible",
                    pseudoProfanity: "❌ Ce pseudo contient des termes inappropriés",
                    pseudoFormat: "❌ 3 caractères min., lettres, chiffres et _ uniquement",
                    passwordsMatch: "✓ Les mots de passe correspondent",
                    passwordsNoMatch: "❌ Les mots de passe ne correspondent pas"
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
                    cancel: "Annuler",
                    noGamesPlayed: "Aucune partie jouée pour l'instant !",
                    loginToSeeScores: "Connectez-vous pour voir vos scores"
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
                    backToMenu: "← Retour au menu d'aide",
                    gamesPageTitle: "🎮 Tutoriels de jeux",
                    si3lnTitle: "SI3LN - Space Invaders III Last Night",
                    howToPlay: "📖 Comment jouer",
                    si3lnDesc: "SI3LN est une version moderne du classique Space Invaders.",
                    controlsTitle: "🎮 Contrôles",
                    ctrlMove: "Flèches ou WASD — Déplacer le vaisseau",
                    ctrlShoot: "Espace — Tirer",
                    ctrlPause: "P — Mettre en pause",
                    ctrlExit: "ESC — Retour au menu",
                    gameplayTitle: "🎯 Gameplay",
                    gameplay1: "Détruisez tous les envahisseurs avant qu'ils atteignent le bas",
                    gameplay2: "Utilisez les barrières comme couverture, elles se dégradent",
                    gameplay3: "Attention à l'OVNI - il donne des points bonus !",
                    gameplay4: "Complétez les niveaux pour débloquer de nouveaux mondes",
                    scoringTitle: "🏆 Score",
                    score1: "Petits aliens : 10 points",
                    score2: "Aliens moyens : 20 points",
                    score3: "Grands aliens : 30 points",
                    score4: "OVNI : 50-300 points (aléatoire)",
                    score5: "Bonus de niveau : 1000 points",
                    tipsTitle: "💡 Conseils",
                    tip1: "Prenez votre temps — la précision prime sur la vitesse",
                    tip2: "Utilisez les barrières stratégiquement",
                    tip3: "Observez les patterns de déplacement des aliens",
                    tip4: "Gardez les bonus pour les niveaux suivants",
                    tip5: "Inscrivez-vous pour sauvegarder vos scores !",
                    reportTitle: "⚠️ Signaler un joueur",
                    reportDesc: "Aidez-nous à maintenir une communauté sûre. Remplissez le formulaire et téléchargez le rapport pour l'envoyer à notre équipe de modération.",
                    reportUsernameLbl: "Nom d'utilisateur *",
                    reportUsernamePh: "Entrez le nom d'utilisateur à signaler",
                    reportReasonLbl: "Raison du signalement *",
                    reportReasonPh: "Sélectionnez une raison",
                    reportReasonOffUser: "Pseudo offensant",
                    reportReasonOffDesc: "Description de profil offensante",
                    reportReasonHaras: "Harcèlement",
                    reportReasonCheat: "Triche/Hack",
                    reportReasonSpam: "Spam",
                    reportReasonOther: "Autre",
                    reportDetailsLbl: "Détails *",
                    reportDetailsPh: "Décrivez l'incident en détail...",
                    reportEvidenceLbl: "Preuves (optionnel)",
                    reportEvidencePh: "Décrivez les preuves disponibles (captures d'écran, date/heure, etc.)",
                    reportSubmitBtn: "📥 Télécharger le rapport",
                    reportNote: "Note : Le rapport sera téléchargé en .txt. Vous pouvez l'envoyer à support@arcad3x.com ou l'uploader via le panel admin. Les faux signalements peuvent entraîner des mesures contre votre compte.",
                    bugPageTitle: "🐛 Signaler un bug",
                    bugDesc: "Vous avez trouvé un bug ? Remplissez le formulaire et téléchargez le rapport.",
                    bugTitleLbl: "Titre du bug *",
                    bugTitlePh: "Description courte du bug",
                    bugCategoryLbl: "Catégorie *",
                    bugCategoryPh: "Sélectionnez une catégorie",
                    bugCatGameplay: "Gameplay",
                    bugCatUI: "Interface utilisateur",
                    bugCatLogin: "Connexion/Authentification",
                    bugCatProfile: "Profil",
                    bugCatGraphics: "Graphismes/Visuel",
                    bugCatAudio: "Audio",
                    bugCatPerf: "Performance",
                    bugCatOther: "Autre",
                    bugDescLbl: "Description *",
                    bugDescPh: "Que s'est-il passé ? Que vous attendiez-vous ?",
                    bugStepsLbl: "Étapes pour reproduire",
                    bugStepsPh: "1. Aller à...\n2. Cliquer sur...\n3. Voir l'erreur",
                    bugBrowserLbl: "Navigateur & OS",
                    bugBrowserPh: "ex : Chrome 120 sur Windows 11",
                    bugSubmitBtn: "📥 Télécharger le rapport de bug",
                    supportTitle: "💝 Soutenir ARCAD3X",
                    supportThankYou: "Merci pour votre soutien !",
                    supportDesc2: "ARCAD3X est un projet passionné créé par des développeurs dévoués. Votre soutien nous aide à continuer d'améliorer la plateforme et à créer de nouveaux jeux.",
                    supportWaysTitle: "Comment nous soutenir",
                    supportWay1: "⭐ Jouez à nos jeux et partagez avec vos amis",
                    supportWay2: "💬 Donnez votre avis et signalez des bugs",
                    supportWay3: "📢 Suivez-nous sur les réseaux sociaux",
                    supportWay4: "💰 Soutien financier (Bientôt disponible)",
                    supportPaymentTitle: "💳 Options de paiement (PayPal, Stripe) bientôt disponibles !",
                    supportPaymentHint: "Nous travaillons à l'intégration de méthodes de paiement sécurisées pour accepter les dons.",
                    supportFooter: "Créé avec ❤️ par Hugex & Schps"
                },
                // Search
                search: {
                    noResults: "Aucun résultat trouvé"
                },
                // Settings page
                settings: {
                    title: "⚙️ Paramètres",
                    language: "Langue",
                    changeLanguage: "Changer de langue"
                },
                // About page
                about: {
                    title: "ℹ️ À propos de nous",
                    description: "Projet SI3LN par Hugex & Schps",
                    platform: "Plateforme de jeu FullStack",
                    copyright: "© 2026 ARCAD3X - Tous droits réservés"
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
