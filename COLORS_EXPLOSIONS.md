# 🎨 Configuration des Couleurs et Explosions - SI3LN

## ✅ Modifications effectuées

### 🎯 Balles (Bullets)
Les balles sont **animées avec des couleurs** définies dans `constants.py` :

#### Space World
- **Joueur** : Noir/Gris foncé (50,50,50) → (20,20,20)
- **Ennemi** : Rose/Magenta (255,50,150) → (255,150,200)

#### Desert World  
- **Joueur** : Jaune/Or (255,200,0) → (255,255,100)
- **Ennemi** : Orange/Marron (200,100,0) → (255,150,50)

#### Forest World
- **Joueur** : Violet/Bleu (100,50,200) → (50,100,255)
- **Ennemi** : Rouge/Noir (200,0,0) → (50,0,0)

#### Marine World
- **Joueur** : Jaune/Anis (200,255,0) → (150,200,50)
- **Ennemi** : Blanc/Émeraude (255,255,255) → (50,255,150)

#### Apocalyptic World
- **Joueur** : Rouge sang (180,0,0) → (100,0,0)
- **Ennemi** : Noir/Pétrole (20,20,20) → (50,80,80)

### 💥 Explosions
Les explosions utilisent maintenant des **images spécifiques** par monde :

- **pb_space.png / eb_space.png** → Explosions dans Space World
- **pb_desert.png / eb_desert.png** → Explosions dans Desert World
- **pb_forest.png / eb_forest.png** → Explosions dans Forest World
- **pb_marine.png / eb_marine.png** → Explosions dans Marine World
- **pb_apocaliptyc.png / eb_apocaliptyc.png** → Explosions dans Apocalyptic World

**pb_** = Explosion quand le joueur meurt  
**eb_** = Explosion quand un ennemi meurt

### 🌍 Backgrounds
Chaque monde charge maintenant son propre fond d'écran automatiquement.

## 📂 Fichiers modifiés

1. **constants.py** - Ajout des couleurs de balles dans WORLDS
2. **game.py** - Chargement dynamique des backgrounds et explosions
3. **entities.py** - Classe Explosion modifiée pour accepter des images
4. **utils.py** - Fonction create_bullet_surface() ajoutée

## 🎮 Comment tester

1. Lance le jeu : `python3 main.py`
2. Sélectionne différents mondes
3. Observe les couleurs de balles changer
4. Détruit des ennemis pour voir les explosions
5. Change de monde pour voir les différents effets !

## 🔧 Comment modifier les couleurs

**Fichier :** `constants.py`

```python
"bullet_colors": {
    "player": [(R1, G1, B1), (R2, G2, B2)],  # [extérieur, intérieur]
    "enemy": [(R1, G1, B1), (R2, G2, B2)]
}
```

Où R, G, B sont des valeurs entre 0 et 255.
