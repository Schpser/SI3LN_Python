"""
Constants and configuration for SI3LN Game
"""
import os

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else '.'
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Screen settings
DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (173, 216, 230)
SAND_COLOR = (210, 180, 140)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)

# Game settings
MAX_LIVES = 5
MAX_PLAYER_BULLETS = 3
PLAYER_SPEED = 8
ENEMY_SPEED = 1
PLAYER_BULLET_SPEED = 10
ENEMY_BULLET_SPEED = 5

# Worlds configuration
WORLDS = {
    "Space": {
        "name": "Space World",
        "background": "background_space.jpg",
        "levels": 5,
        "enemies_dir": "Space_world",
        "enemy_count": 15,
        "bullet_colors": {
            "player": [(0, 150, 255), (100, 200, 255)],      # Bleu électrique
            "enemy": [(255, 50, 150), (255, 150, 200)]        # Rose/Magenta
        }
    },
    "Desert": {
        "name": "Desert World",
        "background": "background_desert.png",
        "levels": 5,
        "enemies_dir": "Desert_world",
        "enemy_count": 8,
        "bullet_colors": {
            "player": [(255, 200, 0), (255, 255, 100)],       # Jaune/Or
            "enemy": [(200, 100, 0), (255, 150, 50)]          # Orange/Marron
        }
    },
    "Forest": {
        "name": "Forest World",
        "background": "background_forest.png",
        "levels": 5,
        "enemies_dir": "Forest_world",
        "enemy_count": 9,
        "bullet_colors": {
            "player": [(50, 255, 150), (150, 255, 200)],      # Vert émeraude
            "enemy": [(150, 50, 200), (200, 100, 255)]        # Violet
        }
    },
    "Marine": {
        "name": "Marine World",
        "background": "background_marine.jpg",
        "levels": 5,
        "enemies_dir": "Marine_world",
        "enemy_count": 12,
        "bullet_colors": {
            "player": [(0, 255, 255), (150, 255, 255)],       # Cyan brillant
            "enemy": [(255, 100, 0), (255, 200, 100)]         # Orange vif
        }
    },
    "Apocalyptic": {
        "name": "Apocalyptic World",
        "background": "background_apocalyptic.jpg",
        "levels": 5,
        "enemies_dir": "Apocalyptic_world",
        "enemy_count": 9,
        "bullet_colors": {
            "player": [(255, 50, 50), (255, 150, 150)],       # Rouge sang
            "enemy": [(0, 255, 0), (150, 255, 150)]           # Vert toxique
        }
    }
}

# Game states
STATE_MAIN_MENU = "MAIN_MENU"
STATE_LOGIN = "LOGIN"
STATE_REGISTER = "REGISTER"
STATE_PLAYER_SELECT = "PLAYER_SELECT"
STATE_LEVEL_SELECT = "LEVEL_SELECT"
STATE_GAMEPLAY = "GAMEPLAY"
STATE_LEVEL_WIN = "LEVEL_WIN"
STATE_GAME_OVER = "GAME_OVER"
STATE_PROFILE = "PROFILE"
STATE_HELP = "HELP"

# File paths
USER_DATA_FILE = os.path.join(DATA_DIR, "users.json")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")

# UI Settings
BUTTON_CORNER_RADIUS = 10
PROFILE_ICON_SIZE = 60
PROFILE_ICON_POSITION = (20, 20)  # Top right offset from screen width

# Email settings (for future password reset functionality)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
