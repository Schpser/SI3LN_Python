"""
Utils package for SI3LN Game
"""
# Import logger functions
from .logger import get_logger, setup_logging

# Import utility functions from game_utils
from .game_utils import (
    load_image,
    draw_text,
    load_enemy_images,
    load_boss_images,
    create_bullet_surface,
    safe_load_image,
    get_asset_path,
    create_circular_surface,
    clamp,
    validate_email,
    hash_password
)

__all__ = [
    'get_logger', 'setup_logging',
    'load_image', 'draw_text', 'load_enemy_images', 'load_boss_images',
    'create_bullet_surface', 'safe_load_image', 'get_asset_path',
    'create_circular_surface', 'clamp', 'validate_email', 'hash_password'
]

