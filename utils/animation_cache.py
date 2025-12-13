"""
Persistent animation cache system
Saves and loads animation frames to/from disk to avoid reloading on every game start
"""
import os
import pickle
import hashlib
from pathlib import Path
from constants import DATA_DIR, BASE_DIR

# Cache directory
CACHE_DIR = Path(DATA_DIR) / "animation_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Metadata file to track cache validity
METADATA_FILE = CACHE_DIR / "cache_metadata.pkl"


def get_cache_file_path(player_index, width, height):
    """Get the cache file path for a specific animation"""
    cache_filename = f"player_{player_index + 1}_{width}x{height}.pkl"
    return CACHE_DIR / cache_filename


def get_folder_hash(player_path):
    """Calculate a hash of all frame files in a folder to detect changes"""
    if not os.path.exists(player_path):
        return None
    
    frame_files = sorted([
        f for f in os.listdir(player_path) 
        if (f.lower().startswith('frame_') or f.lower().startswith('animatediff_')) 
        and f.lower().endswith('.png')
    ])
    
    if not frame_files:
        return None
    
    # Create hash from filenames and modification times
    hash_data = []
    for frame_file in frame_files:
        frame_path = os.path.join(player_path, frame_file)
        if os.path.exists(frame_path):
            mtime = os.path.getmtime(frame_path)
            size = os.path.getsize(frame_path)
            hash_data.append(f"{frame_file}:{mtime}:{size}")
    
    if not hash_data:
        return None
    
    hash_str = "|".join(hash_data)
    return hashlib.md5(hash_str.encode()).hexdigest()


def load_cache_metadata():
    """Load cache metadata from disk"""
    if not METADATA_FILE.exists():
        return {}
    
    try:
        with open(METADATA_FILE, 'rb') as f:
            return pickle.load(f)
    except Exception:
        return {}


def save_cache_metadata(metadata):
    """Save cache metadata to disk"""
    try:
        with open(METADATA_FILE, 'wb') as f:
            pickle.dump(metadata, f)
    except Exception as e:
        print(f"⚠️ Erreur lors de la sauvegarde du cache: {e}")


def load_cached_frames(player_index, width, height, player_path):
    """
    Load frames from cache if available and valid
    
    Returns:
        list of pygame.Surface or None if cache is invalid/missing
    """
    import pygame
    
    cache_file = get_cache_file_path(player_index, width, height)
    
    if not cache_file.exists():
        return None
    
    # Check if source files have changed
    current_hash = get_folder_hash(player_path)
    if current_hash is None:
        return None
    
    metadata = load_cache_metadata()
    cache_key = f"player_{player_index + 1}_{width}x{height}"
    
    # Check if cache is still valid
    if cache_key in metadata:
        cached_hash = metadata[cache_key].get('hash')
        if cached_hash != current_hash:
            # Source files changed, invalidate cache
            try:
                cache_file.unlink()
            except:
                pass
            return None
    
    # Load from cache
    try:
        with open(cache_file, 'rb') as f:
            # Load serialized frame data
            frame_data_list = pickle.load(f)
            
            # Convert back to pygame.Surface objects
            frames = []
            for frame_data in frame_data_list:
                # frame_data is a tuple: (width, height, format, pixels_string)
                w, h, fmt, pixels = frame_data
                # Use fromstring for older pygame, frombytes for newer
                try:
                    surface = pygame.image.fromstring(pixels, (w, h), fmt)
                except AttributeError:
                    # Newer pygame versions use frombytes
                    surface = pygame.image.frombytes(pixels, (w, h), fmt)
                frames.append(surface)
            
            return frames
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement du cache: {e}")
        # Try to remove corrupted cache file
        try:
            cache_file.unlink()
        except:
            pass
        return None


def save_cached_frames(player_index, width, height, frames, player_path):
    """
    Save frames to cache
    
    Args:
        player_index: Index of the player (0-based)
        width: Width of frames
        height: Height of frames
        frames: List of pygame.Surface objects
        player_path: Path to the player folder (for hash calculation)
    """
    import pygame
    
    cache_file = get_cache_file_path(player_index, width, height)
    
    try:
        # Serialize frames to a format that can be pickled
        # Convert each Surface to a serializable format
        frame_data_list = []
        for frame in frames:
            # Get the format and pixels
            # Check if surface has alpha channel
            has_alpha = frame.get_flags() & pygame.SRCALPHA
            fmt = "RGBA" if has_alpha else "RGB"
            
            # Use tostring for older pygame, tobytes for newer
            try:
                pixels = pygame.image.tostring(frame, fmt)
            except AttributeError:
                # Newer pygame versions use tobytes
                pixels = pygame.image.tobytes(frame, fmt)
            
            w, h = frame.get_size()
            frame_data_list.append((w, h, fmt, pixels))
        
        # Save serialized frame data
        with open(cache_file, 'wb') as f:
            pickle.dump(frame_data_list, f)
        
        # Update metadata
        metadata = load_cache_metadata()
        cache_key = f"player_{player_index + 1}_{width}x{height}"
        folder_hash = get_folder_hash(player_path)
        
        metadata[cache_key] = {
            'hash': folder_hash,
            'frame_count': len(frames),
            'width': width,
            'height': height
        }
        
        save_cache_metadata(metadata)
        return True
    except Exception as e:
        print(f"⚠️ Erreur lors de la sauvegarde du cache: {e}")
        return False


def clear_animation_cache():
    """Clear all cached animation files"""
    try:
        # Remove all cache files
        for cache_file in CACHE_DIR.glob("player_*.pkl"):
            cache_file.unlink()
        
        # Remove metadata
        if METADATA_FILE.exists():
            METADATA_FILE.unlink()
        
        return True
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage du cache: {e}")
        return False

