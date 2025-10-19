# SI3LN - Space Invaders III Last Night

Un jeu de type Space Invaders développé en Python avec Pygame, avec un système complet de gestion des utilisateurs, des scores et des niveaux.

## 🎮 Fonctionnalités

### Menu Principal
- **START** : Commencer à jouer en mode invité (pas de sauvegarde des scores)
- **CONTINUE** : Se connecter avec un compte existant
- **AIDE** : Afficher les contrôles
- **QUITTER** : Fermer le jeu

### Système d'Authentification
- **Création de compte** : Pseudo, mot de passe et email (optionnel)
- **Connexion** : Accès aux scores sauvegardés et progression
- **Mode invité** : Jouer sans créer de compte (scores non sauvegardés)

### Sélection de Personnage
- 7+ personnages différents disponibles
- Modification possible à tout moment via le profil

### Sélection de Niveaux
- Organisation par **mondes** (actuellement: Space World)
- Plusieurs **niveaux par monde** (5 niveaux dans Space World)
- Système extensible pour ajouter d'autres mondes

### Gameplay
- Contrôles : 
  - **Flèches directionnelles** ou **WASD** : Déplacement
  - **ESPACE** : Tirer
  - **F11** : Plein écran
  - **ESC** : Retour/Pause
- Ennemis avec patterns de mouvement et tirs
- Système de vies (5 vies par défaut)
- Score basé sur les ennemis détruits et le niveau
- Effets visuels (explosions)

### Profil Utilisateur
- **Icône circulaire** en haut à droite de l'écran (cliquable)
- Modification du personnage
- Changement de pseudo (si disponible)
- Changement de mot de passe
- Affichage des statistiques

### Système de Scores
- **Top 20** des meilleurs scores
- Sauvegarde permanente (fichier JSON)
- Affichage à la fin de chaque partie
- Association avec le compte utilisateur

### Écran de Game Over
- Affichage du score final et niveau atteint
- **Top 10** des meilleurs scores
- Boutons :
  - **RESTART** : Retour à la sélection de niveau
  - **FINISH** : Retour au menu principal

### Adaptation d'Écran
- **Redimensionnement** de la fenêtre supporté
- **Mode plein écran** (F11)
- Interface responsive qui s'adapte automatiquement
- Gestion des différentes résolutions

### Limites de Jeu
- Les joueurs et ennemis restent dans la zone de jeu
- Collisions précises
- Pas de dépassement hors écran

## 📁 Structure du Projet

```
SI3LN_Python/
├── main.py              # Point d'entrée du jeu
├── game.py              # Classe principale du jeu
├── constants.py         # Constantes et configuration
├── utils.py             # Fonctions utilitaires
├── auth.py              # Système d'authentification
├── scores.py            # Gestion des scores
├── profile.py           # Écran de profil
├── level_selector.py    # Sélection des niveaux
├── entities.py          # Entités du jeu (Player, Enemy, Bullet)
├── ui_components.py     # Composants d'interface
├── requirements.txt     # Dépendances Python
├── data/                # Données sauvegardées
│   ├── users.json       # Comptes utilisateurs
│   └── scores.json      # Meilleurs scores
└── assets/              # Ressources du jeu
    ├── players/         # Images des personnages
    ├── enemies/         # Images des ennemis
    ├── sprites/         # Sprites (bullets, etc.)
    └── worlds/          # Backgrounds
```

## 🚀 Installation et Lancement

### Prérequis
- Python 3.7+
- Pygame 2.5.1+

### Installation
```bash
# Cloner le projet
cd /root/SI3LN_Python

# Installer les dépendances
pip install -r requirements.txt
```

### Lancement
```bash
python3 main.py
```

## 🎯 Comment Jouer

1. **Première fois** :
   - Cliquez sur **START** pour jouer en invité
   - Ou créez un compte via **CONTINUE** → **Créer un compte**

2. **Sélection** :
   - Choisissez votre personnage (optionnel si invité)
   - Sélectionnez le monde et le niveau

3. **Jouez** :
   - Déplacez votre vaisseau avec les flèches
   - Tirez avec ESPACE
   - Évitez les tirs ennemis
   - Détruisez tous les ennemis pour gagner

4. **Profil** :
   - Cliquez sur l'icône en haut à droite
   - Modifiez votre personnage, pseudo ou mot de passe

5. **Après une partie** :
   - Consultez le classement
   - RESTART pour rejouer
   - FINISH pour retourner au menu

## 🔧 Configuration

### Ajouter un Monde
Éditez `constants.py` :
```python
WORLDS = {
    "Space": {
        "name": "Space World",
        "background": "background_frozen.jpg",
        "levels": 5,
        "enemies_dir": "Space_world"
    },
    "Desert": {
        "name": "Desert World",
        "background": "background_desert.jpg",
        "levels": 8,
        "enemies_dir": "Desert_world"
    }
}
```

### Modifier les Constantes de Jeu
Dans `constants.py` :
- `MAX_LIVES` : Nombre de vies
- `PLAYER_SPEED` : Vitesse du joueur
- `MAX_PLAYER_BULLETS` : Nombre max de bullets simultanés
- `FPS` : Images par seconde

## 🔐 Sécurité

- Les mots de passe sont hashés avec SHA-256
- Les données sont stockées localement en JSON
- Validation des emails (format basique)
- Protection contre les pseudos en doublon

## 📝 Fonctionnalités Futures

- [ ] Système d'email pour récupération de mot de passe
- [ ] Power-ups (vie supplémentaire, tir multiple, bouclier)
- [ ] Boss de fin de monde
- [ ] Musique et effets sonores
- [ ] Multijoueur local
- [ ] Achievements/Succès
- [ ] Skins supplémentaires déblocables
- [ ] Mode histoire avec cinématiques

## 🐛 Problèmes Connus

- L'audio est désactivé par défaut (`SDL_AUDIODRIVER=dummy`)
- Les performances peuvent varier selon la résolution d'écran

## 👥 Crédits

Développé avec ❤️ en Python et Pygame

## 📄 Licence

Ce projet est à usage éducatif.

---

**Bon jeu ! 🚀**
