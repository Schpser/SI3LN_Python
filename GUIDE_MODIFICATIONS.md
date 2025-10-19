# 🎮 SI3LN - Guide de Modification Rapide

## 📝 Modifier les textes des pop-ups

**Fichier:** `game.py`  
**Lignes:** 188-232

```python
# ==========================================
# 📝 MODIFIER LES TEXTES DES POP-UPS ICI
# ==========================================

# Contenu de la pop-up AIDE
help_content = [
    "=== CONTROLES ===",
    "",
    "Deplacement: Fleches ou WASD",
    "Tirer: ESPACE",
    ...
]

# Contenu de la pop-up GAME (Présentation du jeu)
game_content = [
    "=== SI3LN ===",
    "Space Invaders III Last Night",
    ...
]
```

## 🎨 Style des boutons

**Fichier:** `game.py`  
**Police:** Arcade Classic (chargée automatiquement)  
**Style:** Fond transparent, texte blanc, contour visible

## 🌍 Configuration des mondes

**Fichier:** `constants.py`  
**Variable:** `WORLDS`

Chaque monde a :
- `name`: Nom affiché
- `background`: Fichier image du fond
- `levels`: Nombre de niveaux
- `enemies_dir`: Dossier des ennemis
- `enemy_count`: Nombre d'ennemis

## 🚀 Flux du jeu

1. **Menu Principal**
   - START → Mode invité → Sélection des mondes
   - PLAY → Connexion → Sélection des mondes
   - AIDE → Pop-up avec contrôles
   - GAME → Pop-up avec présentation
   - QUITTER → Ferme le jeu

2. **Sélection des mondes**
   - Vue WORLDS: Cartes visuelles des 5 mondes
   - Clic sur un monde → Vue LEVELS
   - Vue LEVELS: Grille de niveaux (1-5)
   - Bouton COMMENCER → Lance le niveau
   - Bouton RETOUR → Retour (WORLDS→Menu, LEVELS→WORLDS)

## 🐛 Problèmes connus et solutions

### Les mondes ne s'affichent pas en image
- **Vérifier:** Les fichiers dans `assets/worlds/`
- **Noms requis:**
  - `background_space.jpg`
  - `background_desert.png`
  - `background_forest.png`
  - `background_marine.jpg`
  - `background_apocalyptic.jpg`

### Le jeu ne se lance pas
- **Vérifier:** Les ennemis dans `assets/enemies/[monde]_world/`
- **Format requis:** `enemy (1).png`, `enemy (2).png`, etc.

### Problèmes de ponctuation
- **Solution:** Les pop-ups utilisent maintenant une police normale
- **Où:** `ui_components.py`, ligne 245 (WorldCard utilise police normale)

## 📂 Structure importante

```
assets/
├── fonts/
│   └── ArcadeClassic/
│       └── ArcadeClassic.TTF
├── worlds/
│   ├── background_space.jpg
│   ├── background_desert.png
│   ├── background_forest.png
│   ├── background_marine.jpg
│   └── background_apocalyptic.jpg
├── enemies/
│   ├── Space_world/
│   ├── Desert_world/
│   ├── Forest_world/
│   ├── Marine_world/
│   └── Apocalyptic_world/
└── players/
    ├── 1000055338.png (Personnage 1)
    └── ... (8 personnages au total)
```

## ⚙️ Fichiers principaux

- `main.py` - Point d'entrée
- `game.py` - Logique principale du jeu
- `level_selector.py` - Sélection des mondes et niveaux
- `constants.py` - Configuration (mondes, couleurs, constantes)
- `ui_components.py` - Composants UI (boutons, pop-ups, etc.)
- `entities.py` - Joueur, ennemis, bullets
- `auth.py` - Système d'authentification
- `profile.py` - Écran de profil
- `utils.py` - Fonctions utilitaires

## 🎯 Changements récents

✅ Police Arcade Classic pour les boutons et titres  
✅ Police normale pour les textes avec ponctuation  
✅ Bouton CONTINUE renommé en PLAY  
✅ Nouveau sélecteur de mondes avec cartes visuelles  
✅ Pop-ups AIDE et GAME fonctionnelles  
✅ Réduction de l'opacité de l'overlay sur les cartes de mondes  
✅ Correction du bug `self.enemy_images[self.current_world]`
