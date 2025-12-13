"""
Utility functions for SI3LN Game
"""
import pygame
import os
from constants import ASSETS_DIR


def get_asset_path(relative_path):
    """Get absolute path to an asset file"""
    return os.path.join(ASSETS_DIR, relative_path)


def load_image(path, size=None, convert_alpha=True):
    """
    Load an image with error handling
    Returns the image or a colored surface if loading fails
    
    DEPRECATED: Use safe_load_image instead for better error handling
    """
    return safe_load_image(path, size, convert_alpha)


def safe_load_image(path, size=None, convert_alpha=True, fallback_color=None):
    """
    Safely load an image with comprehensive error handling and logging
    
    Args:
        path: Relative path to the image from assets directory
        size: Optional tuple (width, height) to scale the image
        convert_alpha: Whether to use convert_alpha() for transparency
        fallback_color: Optional RGB tuple for fallback surface (default: from constants)
        
    Returns:
        pygame.Surface: The loaded image or a fallback colored surface
    """
    from constants import FALLBACK_IMAGE_COLOR
    
    try:
        full_path = get_asset_path(path)
        
        if not os.path.exists(full_path):
            # Use print to avoid circular import, logger will be used in game.py
            print(f"⚠️ Image file not found: {path} (full path: {full_path})")
            return _create_fallback_surface(size, fallback_color or FALLBACK_IMAGE_COLOR)
        
        if convert_alpha:
            img = pygame.image.load(full_path).convert_alpha()
        else:
            img = pygame.image.load(full_path).convert()
        
        if size:
            img = pygame.transform.scale(img, size)
        
        return img
    except pygame.error as e:
        print(f"⚠️ Pygame error loading image {path}: {e}")
        return _create_fallback_surface(size, fallback_color or FALLBACK_IMAGE_COLOR)
    except Exception as e:
        print(f"⚠️ Unexpected error loading image {path}: {e}")
        return _create_fallback_surface(size, fallback_color or FALLBACK_IMAGE_COLOR)


def _create_fallback_surface(size, color):
    """Create a fallback surface with specified size and color"""
    if size:
        surf = pygame.Surface(size)
    else:
        surf = pygame.Surface((100, 100))
    surf.fill(color)
    return surf


def draw_text(screen, text, font, color, x, y, centered=False):
    """Draw text on screen with optional centering"""
    text_surf = font.render(text, True, color)
    if centered:
        text_rect = text_surf.get_rect(center=(x, y))
        screen.blit(text_surf, text_rect)
    else:
        screen.blit(text_surf, (x, y))
    return text_surf.get_rect(topleft=(x, y))


def create_bullet_surface(color1, color2, size=(8, 20)):
    """
    Create a bullet surface with two colors (gradient effect)
    color1: outer color
    color2: inner color
    size: (width, height) tuple
    """
    bullet = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.ellipse(bullet, color1, (0, 0, size[0], size[1]))
    pygame.draw.ellipse(bullet, color2, (1, 2, size[0]-2, size[1]-4))
    return bullet


def create_circular_surface(image, size):
    """Create a circular cropped version of an image"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    # Draw circle mask
    pygame.draw.circle(surface, (255, 255, 255), (size//2, size//2), size//2)
    
    # Scale image
    scaled_image = pygame.transform.scale(image, (size, size))
    
    # Apply circular mask
    result = pygame.Surface((size, size), pygame.SRCALPHA)
    for x in range(size):
        for y in range(size):
            distance = ((x - size//2) ** 2 + (y - size//2) ** 2) ** 0.5
            if distance <= size // 2:
                result.set_at((x, y), scaled_image.get_at((x, y)))
    
    return result


def clamp(value, min_value, max_value):
    """Clamp a value between min and max"""
    return max(min_value, min(value, max_value))


def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def hash_password(password):
    """Simple password hashing (in production, use bcrypt or similar)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def load_enemy_images(world_name, size=(60, 60)):
    """
    Load all enemy images for a specific world
    Returns a list of enemy images (excluding boss enemies)
    """
    from constants import WORLDS
    import glob
    
    if world_name not in WORLDS:
        return []
    
    enemies_dir = WORLDS[world_name]["enemies_dir"]
    enemy_path = get_asset_path(f"enemies/{enemies_dir}")
    
    # Load regular enemies (not boss enemies)
    enemy_images = []
    
    # Try different patterns
    patterns = [
        os.path.join(enemy_path, "enemy (*.png"),
        os.path.join(enemy_path, "enemy_*.png"),
        os.path.join(enemy_path, "enemy*.png")
    ]
    
    enemy_files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        # Filter out boss enemies
        files = [f for f in files if 'boss' not in f.lower()]
        enemy_files.extend(files)
    
    # Remove duplicates and sort
    enemy_files = sorted(list(set(enemy_files)))
    
    # If no files found with patterns, try listing directory
    if not enemy_files:
        try:
            all_files = os.listdir(enemy_path)
            enemy_files = [
                os.path.join(enemy_path, f) 
                for f in all_files 
                if f.endswith('.png') and 'boss' not in f.lower() and 'enemy' in f.lower()
            ]
        except:
            pass
    
    # Load images
    for file_path in enemy_files:
        try:
            img = pygame.image.load(file_path).convert_alpha()
            img = pygame.transform.scale(img, size)
            enemy_images.append(img)
        except Exception as e:
            print(f"Could not load enemy image {file_path}: {e}")
    
    # If no enemies loaded, create fallback
    if not enemy_images:
        surf = pygame.Surface(size)
        surf.fill((255, 100, 100))
        enemy_images.append(surf)
    
    return enemy_images


def load_boss_images(world_name, size=(100, 100)):
    """
    Load boss enemy images for a specific world
    Returns a list of boss images or None if no boss exists
    """
    from constants import WORLDS
    import glob
    
    if world_name not in WORLDS:
        return []
    
    enemies_dir = WORLDS[world_name]["enemies_dir"]
    enemy_path = get_asset_path(f"enemies/{enemies_dir}")
    
    # Load boss enemies
    boss_images = []
    
    # Try different patterns for boss
    patterns = [
        os.path.join(enemy_path, "boss_enemy*.png"),
        os.path.join(enemy_path, "boss*.png")
    ]
    
    boss_files = []
    for pattern in patterns:
        files = glob.glob(pattern)
        boss_files.extend(files)
    
    # Remove duplicates and sort
    boss_files = sorted(list(set(boss_files)))
    
    # Load images
    for file_path in boss_files:
        try:
            img = pygame.image.load(file_path).convert_alpha()
            img = pygame.transform.scale(img, size)
            boss_images.append(img)
        except Exception as e:
            print(f"Could not load boss image {file_path}: {e}")
    
    return boss_images if boss_images else None
