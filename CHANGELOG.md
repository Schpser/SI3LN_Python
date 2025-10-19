# CHANGELOG - SI3LN Game

## Version 2.0.0 - Refonte Complète (2025-10-19)

### 🎉 Nouvelles Fonctionnalités Majeures

#### Système d'Authentification Complet
- ✅ Création de compte avec pseudo, mot de passe et email
- ✅ Connexion sécurisée (mots de passe hashés SHA-256)
- ✅ Mode invité (jouer sans compte)
- ✅ Modification du profil (pseudo, mdp, personnage)
- ✅ Validation des données (format email, unicité pseudo, longueur)

#### Système de Profil Utilisateur
- ✅ Icône de profil circulaire en haut à droite
- ✅ Écran de modification accessible partout
- ✅ Changement de personnage en temps réel
- ✅ Modification du pseudo (si disponible)
- ✅ Changement de mot de passe sécurisé
- ✅ Persistance des préférences

#### Sélection de Niveaux
- ✅ Organisation par mondes
- ✅ Plusieurs niveaux par monde
- ✅ Interface intuitive avec grille de sélection
- ✅ Affichage du monde et niveau sélectionné
- ✅ Bouton retour vers menu principal

#### Système de Scores
- ✅ Top 20 des meilleurs scores
- ✅ Sauvegarde permanente (JSON)
- ✅ Association avec compte utilisateur
- ✅ Affichage après chaque partie
- ✅ Mise en évidence du nouveau score
- ✅ Tri automatique par score décroissant

#### Interface Utilisateur
- ✅ Menu principal redesigné
- ✅ Écrans de connexion/inscription
- ✅ Boutons START/CONTINUE/AIDE/QUITTER
- ✅ Champs de saisie avec placeholder
- ✅ Feedback visuel (messages, couleurs)
- ✅ Panels semi-transparents
- ✅ Boutons avec hover effects

#### Adaptation d'Écran
- ✅ Fenêtre redimensionnable
- ✅ Mode plein écran (F11)
- ✅ Interface responsive
- ✅ Mise à l'échelle automatique des assets
- ✅ Repositionnement dynamique des éléments

#### Gameplay Amélioré
- ✅ Contrôles fluides (flèches + WASD)
- ✅ Limitation de la zone de jeu (joueur et ennemis)
- ✅ Système de vies (5 par défaut)
- ✅ Collisions précises
- ✅ Effets visuels (explosions)
- ✅ Difficulté progressive (ennemis plus rapides)
- ✅ HUD informatif (score, niveau, vies)

#### Écrans de Jeu
- ✅ Écran de victoire (niveau terminé)
- ✅ Écran de game over avec scores
- ✅ Boutons RESTART/FINISH
- ✅ Bouton NIVEAU SUIVANT
- ✅ Retour à la sélection de niveau

### 🔧 Architecture

#### Modularité
- ✅ `constants.py` - Configuration centralisée
- ✅ `utils.py` - Fonctions utilitaires
- ✅ `auth.py` - Gestion des comptes
- ✅ `scores.py` - Gestion des scores
- ✅ `entities.py` - Entités du jeu (Player, Enemy, Bullet)
- ✅ `ui_components.py` - Composants réutilisables
- ✅ `profile.py` - Écran de profil
- ✅ `level_selector.py` - Sélection de niveaux
- ✅ `game.py` - Logique principale

#### Sauvegarde des Données
- ✅ Format JSON pour faciliter l'édition
- ✅ Dossier `data/` pour les sauvegardes
- ✅ `users.json` - Comptes utilisateurs
- ✅ `scores.json` - Meilleurs scores

### 🎮 Contrôles

- **Déplacement** : Flèches directionnelles ou WASD
- **Tir** : ESPACE
- **Plein écran** : F11
- **Pause/Retour** : ESC
- **Profil** : Clic sur icône circulaire (haut droite)

### 📊 Système de Score

- **Points par ennemi** : 10 × niveau actuel
- **Exemple** : Niveau 5 = 50 points/ennemi
- **Top 20** : Meilleurs scores sauvegardés
- **Affichage** : Pseudo, score, niveau atteint, date

### 🔐 Sécurité

- ✅ Hashage SHA-256 des mots de passe
- ✅ Validation des entrées utilisateur
- ✅ Prévention des doublons (pseudo)
- ✅ Gestion sécurisée des fichiers JSON
- ✅ Mode invité sans risque de perte de données

### 🎨 Assets Supportés

- **Joueurs** : 8 personnages (PNG, 90×90)
- **Ennemis** : 5 types (PNG, 60×60)
- **Backgrounds** : 2 fonds (JPG, adaptatif)
- **Bullets** : 2 types (PNG, 15×25 et 10×20)

### 📝 Documentation

- ✅ `README.md` - Documentation principale
- ✅ `GUIDE_FR.md` - Guide utilisateur complet
- ✅ `DEVELOPMENT.py` - Guide développeur
- ✅ `CHANGELOG.md` - Historique des versions
- ✅ `test_modules.py` - Script de test

### 🐛 Corrections

- ✅ Collision avec limites de jeu
- ✅ Gestion des erreurs de chargement d'assets
- ✅ Désactivation de l'audio (compatibilité serveur)
- ✅ Validation des entrées utilisateur
- ✅ Gestion des états du jeu
- ✅ Nettoyage des entités hors écran

---

## Version 1.0.0 - Version Initiale

### Fonctionnalités de Base
- Menu simple avec bouton START
- Sélection de personnage basique
- Gameplay Space Invaders classique
- Système de vies
- Ennemis avec patterns de mouvement
- Tirs joueur et ennemis
- Écrans de victoire et défaite

---

## Fonctionnalités Futures

### Version 2.1.0 (Planifiée)
- [ ] Récupération de mot de passe par email
- [ ] Système d'achievements/succès
- [ ] Sauvegarde de progression par monde
- [ ] Déblocage progressif des niveaux
- [ ] Statistiques détaillées (temps de jeu, précision, etc.)

### Version 2.2.0 (Planifiée)
- [ ] Musique et effets sonores
- [ ] Power-ups (vie, vitesse, multishot, bouclier)
- [ ] Boss de fin de monde
- [ ] Animations supplémentaires
- [ ] Particules améliorées

### Version 2.3.0 (Planifiée)
- [ ] Multijoueur local (écran partagé)
- [ ] Mode coopératif
- [ ] Mode compétitif
- [ ] Classements par mode de jeu

### Version 3.0.0 (Vision Long Terme)
- [ ] Mode histoire avec cinématiques
- [ ] Nouveaux mondes (Desert, Ocean, Lava, Ice)
- [ ] Personnages déblocables
- [ ] Skins et cosmétiques
- [ ] Boutique in-game
- [ ] Système de quêtes quotidiennes

---

## Notes de Développement

### Technologies Utilisées
- **Python** 3.10+
- **Pygame** 2.5.1
- **JSON** pour persistence des données
- **Hashlib** pour sécurité

### Structure de Données

#### users.json
```json
{
  "username": {
    "password": "hash_sha256",
    "email": "user@example.com",
    "selected_character": 0,
    "high_score": 1000,
    "levels_completed": {}
  }
}
```

#### scores.json
```json
[
  {
    "username": "player1",
    "score": 5000,
    "level": 10,
    "date": "2025-10-19 14:30:00"
  }
]
```

### Performances
- **FPS Cible** : 60
- **Résolution par défaut** : 1280×720
- **Support** : Redimensionnement et plein écran

---

**Dernière mise à jour** : 19 octobre 2025
**Auteur** : Développé avec ❤️ en Python
