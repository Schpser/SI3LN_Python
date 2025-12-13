"""
UI Components for SI3LN Game
Includes buttons, input fields, and other UI elements
"""
import pygame
from constants import *
import os

# Cache global pour les frames d'animation des personnages
# Structure: {(player_index, width, height): [frames]}
_animation_cache = {}


class Button:
    def __init__(self, x, y, width, height, text, font, 
                 bg_color=None, text_color=WHITE, border_color=WHITE,
                 hover_color=None, border_width=3):
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.hover_color = hover_color or LIGHT_GRAY
        self.border_width = border_width
        self.hovered = False
        self.enabled = True
    
    def draw(self, screen):
        if not self.enabled:
            color = DARK_GRAY
        elif self.hovered:
            color = self.hover_color
        elif self.bg_color:
            color = self.bg_color
        else:
            color = None
        
        # Draw background
        if color:
            pygame.draw.rect(screen, color, self.rect, border_radius=BUTTON_CORNER_RADIUS)
        
        # Draw border
        border_color = self.border_color if self.enabled else DARK_GRAY
        pygame.draw.rect(screen, border_color, self.rect, self.border_width, border_radius=BUTTON_CORNER_RADIUS)
        
        # Draw text
        text_color = self.text_color if self.enabled else GRAY
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos) and self.enabled


class ImageButton(Button):
    """Button with an image"""
    def __init__(self, x, y, width, height, image, font=None, text="",
                 border_color=WHITE, selected=False):
        super().__init__(x, y, width, height, text, font, border_color=border_color)
        # handle missing image with a placeholder
        if image is None:
            placeholder = pygame.Surface((width, height), pygame.SRCALPHA)
            placeholder.fill((80, 80, 80))
            self.image = placeholder
        else:
            self.image = pygame.transform.scale(image, (width, height))
        self.selected = selected
        # Animation state (pulse on selection)
        self.animating = False
        self.anim_start = 0
        self.anim_duration = 800  # ms
    
    def draw(self, screen):
        # Draw image (support simple pulse animation when animating)
        if self.animating:
            now = pygame.time.get_ticks()
            elapsed = now - self.anim_start
            if elapsed >= self.anim_duration:
                self.animating = False
                scale = 1.0
            else:
                # progress 0..1
                prog = elapsed / float(self.anim_duration)
                # simple ease-out-in pulse using sine
                import math
                scale = 1.0 + 0.18 * math.sin(prog * math.pi)

            new_w = int(self.rect.width * scale)
            new_h = int(self.rect.height * scale)
            img = pygame.transform.scale(self.image, (new_w, new_h))
            img_rect = img.get_rect(center=self.rect.center)
            screen.blit(img, img_rect)
            draw_rect = img_rect
        else:
            screen.blit(self.image, self.rect)
            draw_rect = self.rect
        
        # Draw border (thicker if selected)
        border_width = 5 if self.selected else 3
        color = YELLOW if self.selected else (self.hover_color if self.hovered else self.border_color)
        pygame.draw.rect(screen, color, draw_rect, border_width, border_radius=BUTTON_CORNER_RADIUS)
        
        # Draw text if any
        if self.text and self.font:
            text_surf = self.font.render(self.text, True, WHITE)
            text_rect = text_surf.get_rect(center=(self.rect.centerx, self.rect.bottom + 15))
            screen.blit(text_surf, text_rect)

    def start_animation(self):
        """Start the pulse animation for this image button."""
        self.animating = True
        self.anim_start = pygame.time.get_ticks()


class InputField:
    """Text input field"""
    def __init__(self, x, y, width, height, font, label="", placeholder="", 
                 password=False, max_length=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.label = label
        self.placeholder = placeholder
        self.text = ""
        self.password = password
        self.max_length = max_length
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(self.text) < self.max_length:
                self.text += event.unicode
    
    def update(self):
        # Cursor blink
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Blink every 0.5 seconds at 60 FPS
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, screen):
        # Draw label
        if self.label:
            label_surf = self.font.render(self.label, True, WHITE)
            screen.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # Draw background
        bg_color = (40, 40, 40) if self.active else (20, 20, 20)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        
        # Draw border
        border_color = CYAN if self.active else WHITE
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=5)
        
        # Draw text or placeholder
        display_text = self.text if self.text else self.placeholder
        text_color = WHITE if self.text else GRAY
        
        if self.password and self.text:
            display_text = "*" * len(self.text)
        
        text_surf = self.font.render(display_text, True, text_color)
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw cursor
        if self.active and self.cursor_visible and self.text:
            cursor_x = self.rect.x + 10 + text_surf.get_width() + 2
            pygame.draw.line(screen, WHITE, 
                           (cursor_x, self.rect.y + 5),
                           (cursor_x, self.rect.bottom - 5), 2)
    
    def get_text(self):
        return self.text
    
    def clear(self):
        self.text = ""


class ProfileIcon:
    """Circular profile icon button"""
    def __init__(self, x, y, size, image):
        self.x = x
        self.y = y
        self.size = size
        self.image = image
        self.circle_surf = self.create_circular_image(image, size)
        self.rect = pygame.Rect(x, y, size, size)
        self.hovered = False
    
    def create_circular_image(self, image, size):
        """Create circular cropped image"""
        # Scale image
        scaled = pygame.transform.scale(image, (size, size))
        
        # Create circular surface
        result = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw scaled image
        result.blit(scaled, (0, 0))
        
        # Create circular mask
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (size//2, size//2), size//2)
        
        # Apply mask by creating new surface with only circular part
        final = pygame.Surface((size, size), pygame.SRCALPHA)
        for x in range(size):
            for y in range(size):
                dist = ((x - size//2) ** 2 + (y - size//2) ** 2) ** 0.5
                if dist <= size // 2:
                    final.set_at((x, y), result.get_at((x, y)))
        
        return final
    
    def update_image(self, new_image):
        """Update the profile image"""
        self.image = new_image
        self.circle_surf = self.create_circular_image(new_image, self.size)
    
    def draw(self, screen):
        # Draw circular image
        screen.blit(self.circle_surf, (self.x, self.y))
        
        # Draw border (highlight when hovered)
        color = YELLOW if self.hovered else WHITE
        pygame.draw.circle(screen, color, 
                         (self.x + self.size//2, self.y + self.size//2), 
                         self.size//2, 3)
    
    def update(self, mouse_pos):
        # Check if mouse is within circle
        dx = mouse_pos[0] - (self.x + self.size//2)
        dy = mouse_pos[1] - (self.y + self.size//2)
        distance = (dx**2 + dy**2) ** 0.5
        self.hovered = distance <= self.size // 2
    
    def is_clicked(self, pos):
        # Check if click is within circle
        dx = pos[0] - (self.x + self.size//2)
        dy = pos[1] - (self.y + self.size//2)
        distance = (dx**2 + dy**2) ** 0.5
        return distance <= self.size // 2


class Panel:
    """A panel for displaying content with background"""
    def __init__(self, x, y, width, height, bg_color=(30, 30, 30), 
                 border_color=WHITE, border_width=2, alpha=230):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.alpha = alpha
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def draw(self, screen):
        # Draw semi-transparent background
        self.surface.fill((*self.bg_color, self.alpha))
        screen.blit(self.surface, self.rect)
        
        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 
                        self.border_width, border_radius=10)


class PopUp:
    """A popup window that appears in the bottom-right corner"""
    def __init__(self, width, height, title, content, screen_width, screen_height, font, title_font=None):
        self.width = width
        self.height = height
        self.title = title
        self.content = content  # List of strings or images
        self.font = pygame.font.Font(None, 24)  # Police normale pour le contenu (ponctuation OK)
        self.font_title = title_font if title_font else pygame.font.Font(None, 36)
        
        # Position in bottom-right corner with margin
        margin = 20
        self.x = screen_width - width - margin
        self.y = screen_height - height - margin
        
        self.panel = Panel(self.x, self.y, width, height, 
                          bg_color=(20, 20, 40), border_color=CYAN, border_width=3, alpha=240)
        
        # Close button avec police normale
        btn_font = pygame.font.Font(None, 28)
        self.close_btn = Button(self.x + width - 30, self.y + 20, 40, 40, "X", 
                               btn_font, bg_color=(150, 30, 30), text_color=WHITE)
        
        self.visible = False
        self.images = []  # Store loaded images if any
    
    def open(self):
        self.visible = True
    
    def close(self):
        self.visible = False
    
    def draw(self, screen):
        if not self.visible:
            return
        
        # Draw panel
        self.panel.draw(screen)
        
        # Draw title
        title_surf = self.font_title.render(self.title, True, CYAN)
        title_rect = title_surf.get_rect(centerx=self.x + self.width//2, top=self.y + 15)
        screen.blit(title_surf, title_rect)
        
        # Draw content
        y_offset = self.y + 70
        line_height = 30
        
        for item in self.content:
            if isinstance(item, str):
                # Text content
                text_surf = self.font.render(item, True, WHITE)
                text_rect = text_surf.get_rect(left=self.x + 20, top=y_offset)
                screen.blit(text_surf, text_rect)
                y_offset += line_height
            elif isinstance(item, pygame.Surface):
                # Image content
                img_rect = item.get_rect(centerx=self.x + self.width//2, top=y_offset)
                screen.blit(item, img_rect)
                y_offset += item.get_height() + 10
        
        # Draw close button
        self.close_btn.draw(screen)
    
    def update(self, mouse_pos):
        if self.visible:
            self.close_btn.update(mouse_pos)
    
    def handle_click(self, pos):
        if self.visible and self.close_btn.is_clicked(pos):
            self.close()
            return True
        return False


class AnimatedPlayer:
    """Affiche un personnage animé à partir de frames avec cache pour performance"""
    def __init__(self, x, y, width, height, player_index):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.player_index = player_index
        
        # Load frames (utilise le cache si disponible)
        self.frames = []
        self.load_frames()
        
        # Animation variables
        self.current_frame = 0
        self.frame_delay = 1/24  # ~41.67ms per frame for 24fps
        self.elapsed_time = 0.0
        self.is_animating = True
        self.loop = True  # Loop animation
        self.rect = pygame.Rect(x, y, width, height)
    
    def load_frames(self):
        """Load all animation frames for the player (utilise le cache global)"""
        global _animation_cache
        
        # Clé du cache: (player_index, width, height)
        cache_key = (self.player_index, self.width, self.height)
        
        # Vérifier si les frames sont déjà en cache
        if cache_key in _animation_cache:
            self.frames = _animation_cache[cache_key]
            return
        
        # Sinon, charger depuis le disque
        player_path = f"assets/players/player_{self.player_index + 1}"
        
        # Check if folder exists
        if not os.path.exists(player_path):
            print(f"⚠️ Dossier introuvable : {player_path}")
            return
        
        # Load all frame files (supports both formats)
        frame_files = sorted([
            f for f in os.listdir(player_path) 
            if (f.lower().startswith('frame_') or f.lower().startswith('animatediff_')) 
            and f.lower().endswith('.png')
        ])
        
        # Sort by frame number (handles both naming conventions)
        def get_frame_number(filename):
            if filename.lower().startswith('frame_'):
                return int(filename.split('_')[1])
            else:  # AnimateDiff format
                # Extract number from AnimateDiff_00001.XXX.png
                import re
                match = re.search(r'\.(\d+)\.png', filename)
                if match:
                    return int(match.group(1))
                return 999999  # Put invalid files at the end
        
        frame_files.sort(key=get_frame_number)
        
        # Charger et mettre en cache
        start_time = pygame.time.get_ticks()
        for frame_file in frame_files:
            frame_path = os.path.join(player_path, frame_file)
            try:
                image = pygame.image.load(frame_path)
                scaled = pygame.transform.scale(image, (self.width, self.height))
                self.frames.append(scaled)
            except pygame.error as e:
                print(f"⚠️ Impossible de charger {frame_path}: {e}")
        
        # Mettre en cache pour réutilisation future
        if self.frames:
            _animation_cache[cache_key] = self.frames
            elapsed = pygame.time.get_ticks() - start_time
            print(f"✓ {len(self.frames)} frames chargées pour player_{self.player_index + 1} en {elapsed}ms (mis en cache)")
        else:
            print(f"⚠️ Aucune frame chargée pour player_{self.player_index + 1}")
    
    def change_player(self, new_player_index):
        """Change le personnage affiché (utilise le cache si disponible)"""
        if new_player_index == self.player_index:
            return  # Déjà le bon personnage
        
        self.player_index = new_player_index
        self.current_frame = 0
        self.elapsed_time = 0.0
        
        # Recharger les frames (utilise le cache si disponible)
        self.load_frames()
    
    def update(self, dt=1/60):
        """Update animation frame"""
        if not self.frames or not self.is_animating:
            return
        
        # Update elapsed time (dt is delta time in seconds)
        self.elapsed_time += dt
        
        # Check if we should move to next frame
        if self.elapsed_time >= self.frame_delay:
            self.elapsed_time -= self.frame_delay
            self.current_frame += 1
            
            # Handle animation loop
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_animating = False
    
    def draw(self, screen):
        """Draw current frame"""
        if not self.frames:
            return
        
        current_frame_index = min(self.current_frame, len(self.frames) - 1)
        frame = self.frames[current_frame_index]
        screen.blit(frame, (self.x, self.y))
    
    def reset(self):
        """Reset animation to beginning"""
        self.current_frame = 0
        self.elapsed_time = 0.0
        self.is_animating = True
    
    def get_current_frame_image(self):
        """Get the current frame as a static image"""
        if not self.frames:
            return None
        current_frame_index = min(self.current_frame, len(self.frames) - 1)
        return self.frames[current_frame_index]


def preload_character_animations(width, height, max_players=9):
    """Précharge les animations de tous les personnages disponibles dans le cache"""
    global _animation_cache
    
    print("🔄 Préchargement des animations des personnages...")
    start_time = pygame.time.get_ticks()
    loaded_count = 0
    
    for player_index in range(max_players):
        cache_key = (player_index, width, height)
        
        # Vérifier si déjà en cache
        if cache_key in _animation_cache:
            continue
        
        # Charger les frames
        player_path = f"assets/players/player_{player_index + 1}"
        if not os.path.exists(player_path):
            continue
        
        # Load all frame files
        frame_files = sorted([
            f for f in os.listdir(player_path) 
            if (f.lower().startswith('frame_') or f.lower().startswith('animatediff_')) 
            and f.lower().endswith('.png')
        ])
        
        if not frame_files:
            continue
        
        # Sort by frame number
        def get_frame_number(filename):
            if filename.lower().startswith('frame_'):
                return int(filename.split('_')[1])
            else:
                import re
                match = re.search(r'\.(\d+)\.png', filename)
                if match:
                    return int(match.group(1))
                return 999999
        
        frame_files.sort(key=get_frame_number)
        
        # Charger et mettre en cache
        frames = []
        for frame_file in frame_files:
            frame_path = os.path.join(player_path, frame_file)
            try:
                image = pygame.image.load(frame_path)
                scaled = pygame.transform.scale(image, (width, height))
                frames.append(scaled)
            except pygame.error as e:
                print(f"⚠️ Impossible de charger {frame_path}: {e}")
        
        if frames:
            _animation_cache[cache_key] = frames
            loaded_count += 1
    
    elapsed = pygame.time.get_ticks() - start_time
    print(f"✓ {loaded_count} personnages préchargés en {elapsed}ms")


class CharacterSelect:
    """Character selection interface"""
    def __init__(self, screen_width, screen_height, font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        
        # Panel for character info and actions
        self.info_panel = Panel(50, 50, 400, 500, bg_color=(10, 10, 20), border_color=CYAN, border_width=3, alpha=240)
        
        # Character slots (3 rows of 3 slots)
        self.character_slots = []
        slot_width = 120
        slot_height = 120
        for row in range(3):
            for col in range(3):
                x = 100 + col * (slot_width + 20)
                y = 100 + row * (slot_height + 20)
                slot = ImageButton(x, y, slot_width, slot_height, None, font, "", border_color=WHITE)
                self.character_slots.append(slot)
        
        # Les animations sont déjà préchargées au démarrage du jeu (dans Game.load_assets())
        # Pas besoin de les recharger ici - le cache les réutilisera automatiquement
        preview_width = 160
        preview_height = 160
        
        # Selected character index
        self.selected_character = 0
        self.update_selected_character()
        
        # Create animated player preview (positioned on the right side of panel)
        preview_x = self.info_panel.rect.right - 200
        preview_y = self.info_panel.rect.centery - 80
        self.animated_player = AnimatedPlayer(preview_x, preview_y, preview_width, preview_height, self.selected_character)
        
        # Back and Confirm buttons
        self.back_button = Button(50, screen_height - 100, 150, 50, "Back", font, bg_color=(150, 30, 30), text_color=WHITE)
        self.confirm_button = Button(screen_width - 200, screen_height - 100, 150, 50, "Confirm", font, bg_color=(30, 150, 30), text_color=WHITE)
        
        # Pop-up for confirming character selection
        self.confirm_popup = PopUp(300, 200, "Confirm Selection", [], screen_width, screen_height, font)
    
    def update_selected_character(self):
        """Update the selected character and its display"""
        for i, slot in enumerate(self.character_slots):
            slot.selected = (i == self.selected_character)
            # Load character image (placeholder for now)
            if i == self.selected_character:
                # Load actual character image
                char_image_path = f"assets/characters/character_{i + 1}.png"
                if os.path.exists(char_image_path):
                    char_image = pygame.image.load(char_image_path)
                    char_image = pygame.transform.scale(char_image, (slot.rect.width, slot.rect.height))
                    slot.image = char_image
                else:
                    print(f"⚠️ Character image not found: {char_image_path}")
            else:
                slot.image = None  # Clear image for unselected slots
        
        # Update animated player preview (utilise le cache pour performance)
        if self.animated_player.player_index != self.selected_character:
            self.animated_player.change_player(self.selected_character)
        self.animated_player.reset()
    
    def draw_character_info(self, screen):
        """Draw the information of the selected character"""
        char_index = self.selected_character
        info_x = self.info_panel.rect.x + 20
        info_y = self.info_panel.rect.y + 20
        
        # Character name (placeholder)
        name_surf = self.font.render(f"Character {char_index + 1}", True, WHITE)
        screen.blit(name_surf, (info_x, info_y))
        
        # Character description (placeholder)
        desc_surf = self.font.render("This is a placeholder description.", True, GRAY)
        screen.blit(desc_surf, (info_x, info_y + 40))
        
        # Draw the animated player
        self.animated_player.draw(screen)
    
    def draw(self, screen):
        # Draw info panel
        self.info_panel.draw(screen)
        
        # Draw character slots
        for slot in self.character_slots:
            slot.draw(screen)
        
        # Draw buttons
        self.back_button.draw(screen)
        self.confirm_button.draw(screen)
        
        # Draw character info (below slots)
        self.draw_character_info(screen)
        
        # Draw confirmation popup if visible
        self.confirm_popup.draw(screen)
    
    def update(self, mouse_pos):
        # Update character slots
        for slot in self.character_slots:
            slot.update(mouse_pos)
        
        # Update buttons
        self.back_button.update(mouse_pos)
        self.confirm_button.update(mouse_pos)
        
        # Update confirmation popup
        self.confirm_popup.update(mouse_pos)
        
        # Update animated player preview
        self.animated_player.update(1/60)
    
    def handle_click(self, pos):
        # Check character slot clicks
        for i, slot in enumerate(self.character_slots):
            if slot.is_clicked(pos):
                self.selected_character = i
                self.update_selected_character()
                return True
        
        # Check buttons
        if self.back_button.is_clicked(pos):
            # Handle back button (e.g., go to previous menu)
            return True
        elif self.confirm_button.is_clicked(pos):
            # Open confirmation popup
            self.confirm_popup.open()
            # Update popup content with character info
            char_index = self.selected_character
            char_name = f"Character {char_index + 1}"
            char_desc = "This is a placeholder description."
            self.confirm_popup.content = [char_name, char_desc]
            return True
        
        # Check confirmation popup
        if self.confirm_popup.visible:
            if self.confirm_popup.handle_click(pos):
                # Confirm selection (e.g., save and proceed)
                self.confirm_popup.close()
                return True
        
        return False
