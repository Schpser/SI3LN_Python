"""
UI Components for SI3LN Game
Includes buttons, input fields, and other UI elements
"""
import pygame
from constants import *


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
        self.image = pygame.transform.scale(image, (width, height))
        self.selected = selected
    
    def draw(self, screen):
        # Draw image
        screen.blit(self.image, self.rect)
        
        # Draw border (thicker if selected)
        border_width = 5 if self.selected else 3
        color = YELLOW if self.selected else (self.hover_color if self.hovered else self.border_color)
        pygame.draw.rect(screen, color, self.rect, border_width, border_radius=BUTTON_CORNER_RADIUS)
        
        # Draw text if any
        if self.text and self.font:
            text_surf = self.font.render(self.text, True, WHITE)
            text_rect = text_surf.get_rect(center=(self.rect.centerx, self.rect.bottom + 15))
            screen.blit(text_surf, text_rect)


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
