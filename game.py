"""
Main Game class for SI3LN Game
Integrates all screens and game logic
"""
import pygame
import random
import sys
from constants import *
from utils import load_image, draw_text, load_enemy_images, load_boss_images, create_bullet_surface
from auth import AuthSystem
from scores import ScoreManager
from profile import ProfileScreen
from level_selector import LevelSelector
from entities import Player, Enemy, Bullet, Explosion
from ui_components import Button, InputField, ProfileIcon, Panel, PopUp


class Game:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Screen setup with resizable window
        self.screen_info = pygame.display.Info()
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("S I 3 L N")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = STATE_MAIN_MENU
        self.prev_state = None
        
        # Systems
        self.auth = AuthSystem()
        self.score_manager = ScoreManager()
        
        # Game data
        self.current_score = 0
        self.current_level = 1
        self.current_world = "Space"
        self.lives = MAX_LIVES
        self.selected_character = 0
        
        # Load assets
        self.load_assets()
        
        # Initialize screens
        self.profile_screen = ProfileScreen(self.screen, self.auth, self.players)
        self.level_selector = LevelSelector(self.screen, WORLDS)
        
        # Create UI
        self.create_ui()
        
        # Game entities
        self.player = None
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        
        # Profile icon
        self.profile_icon = None
        self.update_profile_icon()
        
        # Fullscreen toggle
        self.is_fullscreen = False
    
    def load_assets(self):
        """Load all game assets"""
        # Fonts - Load Arcade Classic font
        arcade_font_path = "assets/fonts/ArcadeClassic/ArcadeClassic.TTF"
        try:
            self.font_large = pygame.font.Font(arcade_font_path, 70)
            self.font_medium = pygame.font.Font(arcade_font_path, 40)
            self.font_small = pygame.font.Font(arcade_font_path, 28)
            self.font_tiny = pygame.font.Font(arcade_font_path, 20)
        except:
            # Fallback to default font
            self.font_large = pygame.font.Font(None, 70)
            self.font_medium = pygame.font.Font(None, 40)
            self.font_small = pygame.font.Font(None, 28)
            self.font_tiny = pygame.font.Font(None, 20)
        
        # Backgrounds
        self.menu_bg = load_image("worlds/home_page.jpg", 
                                  (self.screen_width, self.screen_height), False)
        
        # Load all world backgrounds
        self.world_backgrounds = {}
        for world_key, world_data in WORLDS.items():
            bg_path = f"worlds/{world_data['background']}"
            self.world_backgrounds[world_key] = load_image(bg_path, 
                                                          (self.screen_width, self.screen_height), False)
        
        # Current game background (will be set when level starts)
        self.game_bg = self.world_backgrounds.get("Space")  # Default to Space
        
        # Players
        self.players = []
        player_files = [
            "1000055338.png", "1000055339.png", "1000055340.png",
            "1000055341.png", "1000055342.png", "1000055343.png",
            "1000055344.png", "1000055345.png"
        ]
        
        for file in player_files:
            img = load_image(f"players/{file}", (90, 90))
            self.players.append(img)
        
        # Bullets - will be created dynamically per world
        # Create default bullets (Space world colors)
        default_colors = WORLDS["Space"]["bullet_colors"]
        self.player_bullet_img = create_bullet_surface(
            default_colors["player"][0], 
            default_colors["player"][1], 
            (15, 25)
        )
        self.enemy_bullet_img = create_bullet_surface(
            default_colors["enemy"][0], 
            default_colors["enemy"][1], 
            (10, 20)
        )
        
        # Enemies - will be loaded per world when level starts
        self.enemy_images = {}  # Dictionary to store enemies per world
        self.boss_images = {}    # Dictionary to store boss images per world
        
        # Preload enemies for all worlds
        for world_key in WORLDS.keys():
            self.enemy_images[world_key] = load_enemy_images(world_key, (60, 60))
            self.boss_images[world_key] = load_boss_images(world_key, (100, 100))
        
        # Current world enemies (default to first world)
        self.current_enemy_images = self.enemy_images.get("Space", [])
    
    def create_ui(self):
        """Create all UI elements"""
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        
        # Main menu buttons - Style arcade avec fond transparent
        self.btn_start = Button(cx, cy - 40, 250, 70, "START", 
                               self.font_medium, bg_color=None, text_color=WHITE, border_color=WHITE)
        self.btn_continue = Button(cx, cy + 50, 250, 70, "PLAY",
                                   self.font_medium, bg_color=None, text_color=WHITE, border_color=WHITE)
        self.btn_help = Button(self.screen_width - 100, self.screen_height - 70,
                              150, 50, "AIDE", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
        self.btn_game = Button(self.screen_width - 100, self.screen_height - 130,
                              150, 50, "GAME", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
        self.btn_quit = Button(self.screen_width - 100, self.screen_height - 190,
                              150, 50, "QUITTER", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
        
        # Login screen
        self.login_username = InputField(cx - 150, cy - 80, 300, 45,
                                        self.font_small, "Pseudo:")
        self.login_password = InputField(cx - 150, cy, 300, 45,
                                        self.font_small, "Mot de passe:", 
                                        password=True)
        self.btn_login = Button(cx, cy + 80, 200, 50, "CONNEXION",
                               self.font_small, bg_color=GREEN)
        self.btn_to_register = Button(cx, cy + 150, 250, 50, "Créer un compte",
                                      self.font_small)
        self.btn_guest = Button(cx, cy + 210, 250, 50, "Mode invité",
                               self.font_small, bg_color=ORANGE)
        
        # Register screen
        self.register_username = InputField(cx - 150, cy - 120, 300, 45,
                                           self.font_small, "Pseudo:")
        self.register_email = InputField(cx - 150, cy - 50, 300, 45,
                                        self.font_small, "Email (optionnel):")
        self.register_password = InputField(cx - 150, cy + 20, 300, 45,
                                           self.font_small, "Mot de passe:",
                                           password=True)
        self.register_confirm = InputField(cx - 150, cy + 90, 300, 45,
                                          self.font_small, "Confirmer:",
                                          password=True)
        self.btn_register = Button(cx, cy + 170, 200, 50, "S'INSCRIRE",
                                   self.font_small, bg_color=GREEN)
        self.btn_back_login = Button(cx, cy + 230, 200, 50, "RETOUR",
                                     self.font_small)
        
        # Game over buttons
        self.btn_restart = Button(cx - 130, self.screen_height - 80,
                                 200, 60, "RESTART", self.font_medium,
                                 bg_color=ORANGE)
        self.btn_finish = Button(cx + 130, self.screen_height - 80,
                                200, 60, "FINISH", self.font_medium,
                                bg_color=RED)
        
        # Level win buttons
        self.btn_next_level = Button(cx, cy + 100, 250, 70, "NIVEAU SUIVANT",
                                     self.font_medium, bg_color=GREEN)
        self.btn_level_select = Button(cx, cy + 190, 250, 70, "CHOIX NIVEAU",
                                       self.font_medium)
        
        # Message display
        self.message = ""
        self.message_color = WHITE
        self.message_timer = 0
        
        # ==========================================
        # 📝 MODIFIER LES TEXTES DES POP-UPS ICI
        # ==========================================
        
        # Contenu de la pop-up AIDE
        # Vous pouvez modifier ces textes comme vous voulez
        help_content = [
            "=== CONTROLES ===",
            "",
            "Deplacement: Fleches ou WASD",
            "Tirer: ESPACE",
            "Plein ecran: F11",
            "Retour menu: ESC",
            "",
            "Detruisez tous les ennemis!",
            "Evitez leurs tirs!"
        ]
        
        # Contenu de la pop-up GAME (Présentation du jeu)
        # Vous pouvez modifier ces textes comme vous voulez
        game_content = [
            "=== SI3LN ===",
            "Space Invaders III Last Night",
            "",
            "Un jeu de tir spatial retro",
            "avec 5 mondes differents!",
            "",
            "- Space World",
            "- Desert World", 
            "- Forest World",
            "- Marine World",
            "- Apocalyptic World",
            "",
            "Survivez aux vagues d'ennemis",
            "et battez les boss!"
        ]
        
        # ==========================================
        # FIN DE LA SECTION TEXTES DES POP-UPS
        # ==========================================
        
        self.popup_help = PopUp(400, 500, "AIDE", help_content, 
                               self.screen_width, self.screen_height, self.font_small, self.font_large)
        self.popup_game = PopUp(400, 500, "A PROPOS DU JEU", game_content,
                               self.screen_width, self.screen_height, self.font_small, self.font_large)
    
    def update_profile_icon(self):
        """Update profile icon with current character"""
        if self.auth.guest_mode:
            char_idx = self.auth.guest_character
        elif self.auth.current_user:
            char_idx = self.auth.get_user_data("selected_character") or 0
        else:
            char_idx = 0
        
        if char_idx < len(self.players):
            icon_x = self.screen_width - PROFILE_ICON_SIZE - PROFILE_ICON_POSITION[0]
            icon_y = PROFILE_ICON_POSITION[1]
            self.profile_icon = ProfileIcon(icon_x, icon_y, PROFILE_ICON_SIZE,
                                           self.players[char_idx])
        
        self.selected_character = char_idx
    
    def show_message(self, text, color=WHITE, duration=180):
        """Show a temporary message"""
        self.message = text
        self.message_color = color
        self.message_timer = duration
    
    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)
            
            # Handle fullscreen toggle (F11)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    if self.profile_screen.active:
                        self.profile_screen.close()
                    elif self.state == STATE_GAMEPLAY:
                        self.state = STATE_LEVEL_SELECT
            
            # Profile screen has priority
            if self.profile_screen.active:
                if self.profile_screen.handle_event(event):
                    self.update_profile_icon()
                continue
            
            # Level selector
            if self.level_selector.active:
                result = self.level_selector.handle_event(event)
                if result:
                    print(f"[DEBUG] Level selector returned: {result}")
                    if result[0] == "START_LEVEL":
                        self.current_world = result[1]
                        self.current_level = result[2]
                        print(f"[DEBUG] Starting world={self.current_world}, level={self.current_level}")
                        self.level_selector.close()  # Close level selector before starting
                        self.start_level()
                    elif result[0] == "BACK":
                        self.level_selector.close()
                        self.state = STATE_MAIN_MENU
                continue
            
            # State-specific event handling
            if self.state == STATE_MAIN_MENU:
                self.handle_main_menu_events(event)
            elif self.state == STATE_LOGIN:
                self.handle_login_events(event)
            elif self.state == STATE_REGISTER:
                self.handle_register_events(event)
            elif self.state == STATE_GAMEPLAY:
                self.handle_gameplay_events(event)
            elif self.state == STATE_GAME_OVER:
                self.handle_game_over_events(event)
            elif self.state == STATE_LEVEL_WIN:
                self.handle_level_win_events(event)
    
    def handle_main_menu_events(self, event):
        """Handle main menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if self.btn_start.is_clicked(pos):
                # Go to character selection and play as guest
                self.auth.login_as_guest(self.selected_character)
                self.update_profile_icon()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            elif self.btn_continue.is_clicked(pos):
                self.state = STATE_LOGIN
            
            elif self.btn_help.is_clicked(pos):
                self.popup_help.open()
            
            elif self.btn_game.is_clicked(pos):
                self.popup_game.open()
            
            elif self.btn_quit.is_clicked(pos):
                self.running = False
            
            # Check popup clicks
            if self.popup_help.handle_click(pos) or self.popup_game.handle_click(pos):
                pass  # Popup handled the click
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.profile_screen.open()
    
    def handle_login_events(self, event):
        """Handle login screen events"""
        self.login_username.handle_event(event)
        self.login_password.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if self.btn_login.is_clicked(pos):
                username = self.login_username.get_text().strip()
                password = self.login_password.get_text()
                
                success, msg = self.auth.login(username, password)
                if success:
                    self.show_message(msg, GREEN)
                    self.update_profile_icon()
                    self.level_selector.open()
                    self.state = STATE_LEVEL_SELECT
                    self.login_username.clear()
                    self.login_password.clear()
                else:
                    self.show_message(msg, RED)
            
            elif self.btn_to_register.is_clicked(pos):
                self.state = STATE_REGISTER
                self.login_username.clear()
                self.login_password.clear()
            
            elif self.btn_guest.is_clicked(pos):
                self.auth.login_as_guest(self.selected_character)
                self.update_profile_icon()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
        
        # ESC to go back
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_MAIN_MENU
                self.login_username.clear()
                self.login_password.clear()
    
    def handle_register_events(self, event):
        """Handle register screen events"""
        self.register_username.handle_event(event)
        self.register_email.handle_event(event)
        self.register_password.handle_event(event)
        self.register_confirm.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if self.btn_register.is_clicked(pos):
                username = self.register_username.get_text().strip()
                email = self.register_email.get_text().strip()
                password = self.register_password.get_text()
                confirm = self.register_confirm.get_text()
                
                if password != confirm:
                    self.show_message("Les mots de passe ne correspondent pas", RED)
                    return
                
                success, msg = self.auth.register(username, password, email)
                if success:
                    self.show_message(msg, GREEN)
                    # Auto login
                    self.auth.login(username, password)
                    self.update_profile_icon()
                    self.state = STATE_MAIN_MENU
                    # Clear fields
                    self.register_username.clear()
                    self.register_email.clear()
                    self.register_password.clear()
                    self.register_confirm.clear()
                else:
                    self.show_message(msg, RED)
            
            elif self.btn_back_login.is_clicked(pos):
                self.state = STATE_LOGIN
                self.register_username.clear()
                self.register_email.clear()
                self.register_password.clear()
                self.register_confirm.clear()
        
        # ESC to go back
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = STATE_LOGIN
    
    def handle_gameplay_events(self, event):
        """Handle gameplay events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.shoot_player_bullet()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.prev_state = self.state
                self.profile_screen.open()
    
    def handle_game_over_events(self, event):
        """Handle game over screen events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if self.btn_restart.is_clicked(pos):
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            elif self.btn_finish.is_clicked(pos):
                self.state = STATE_MAIN_MENU
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.profile_screen.open()
    
    def handle_level_win_events(self, event):
        """Handle level win screen events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if self.btn_next_level.is_clicked(pos):
                self.current_level += 1
                # Check if level exists in current world
                max_levels = WORLDS[self.current_world]["levels"]
                if self.current_level > max_levels:
                    self.show_message("Tous les niveaux terminés!", GREEN)
                    self.level_selector.open()
                    self.state = STATE_LEVEL_SELECT
                else:
                    self.start_level()
            
            elif self.btn_level_select.is_clicked(pos):
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.profile_screen.open()
    
    def start_level(self):
        """Start a new level"""
        print(f"[DEBUG] Starting level {self.current_level} in world {self.current_world}")
        self.state = STATE_GAMEPLAY
        self.lives = MAX_LIVES
        
        # Set the background for the current world
        self.game_bg = self.world_backgrounds.get(self.current_world, self.world_backgrounds["Space"])
        print(f"[DEBUG] Background set for world: {self.current_world}")
        
        # Create bullets with world-specific colors (animated)
        if self.current_world in WORLDS and "bullet_colors" in WORLDS[self.current_world]:
            colors = WORLDS[self.current_world]["bullet_colors"]
            
            # Player bullet - animated with colors
            self.player_bullet_img = create_bullet_surface(
                colors["player"][0], 
                colors["player"][1], 
                (15, 25)
            )
            
            # Enemy bullet - animated with colors
            self.enemy_bullet_img = create_bullet_surface(
                colors["enemy"][0], 
                colors["enemy"][1], 
                (10, 20)
            )
            
            print(f"[DEBUG] Bullets created with colors for {self.current_world}")
        
        # Load explosion images specific to the world
        # Map world names to explosion file names
        explosion_file_map = {
            "Space": ("sprites/player/pb_space.png", "sprites/ennemy/eb_space.png"),
            "Desert": ("sprites/player/pb_desert.png", "sprites/ennemy/eb_desert.png"),
            "Forest": ("sprites/player/pb_forest.png", "sprites/ennemy/eb_forest.png"),
            "Marine": ("sprites/player/pb_marine.png", "sprites/ennemy/eb_marine.png"),
            "Apocalyptic": ("sprites/player/pb_apocaliptyc.png", "sprites/ennemy/eb_apocaliptyc.png")
        }
        
        if self.current_world in explosion_file_map:
            player_exp_path, enemy_exp_path = explosion_file_map[self.current_world]
            try:
                self.player_explosion_img = load_image(player_exp_path, (60, 60))
                self.enemy_explosion_img = load_image(enemy_exp_path, (60, 60))
                print(f"[DEBUG] Loaded explosion images for {self.current_world}")
            except Exception as e:
                print(f"[DEBUG] Could not load explosion images: {e}")
                self.player_explosion_img = None
                self.enemy_explosion_img = None
        else:
            self.player_explosion_img = None
            self.enemy_explosion_img = None
        
        # Clear all entities
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.explosions.empty()
        
        # Create player
        player_img = self.players[self.selected_character]
        self.player = Player(self.screen_width // 2, 
                            self.screen_height - 100,
                            player_img,
                            self.screen_width,
                            self.screen_height)
        
        # Create enemies
        print(f"[DEBUG] Spawning enemies...")
        self.spawn_enemies()
        print(f"[DEBUG] Level started successfully! Enemies: {len(self.enemies)}")
    
    def spawn_enemies(self):
        """Spawn enemies for current level"""
        # Calculate number of enemies based on level
        base_rows = 3
        base_cols = 5
        rows = min(base_rows + self.current_level // 2, 6)
        cols = min(base_cols + self.current_level // 2, 9)
        
        # Calculate spacing
        enemy_width = 60
        enemy_height = 60
        spacing_x = 20
        spacing_y = 20
        
        total_width = cols * (enemy_width + spacing_x)
        start_x = (self.screen_width - total_width) // 2
        start_y = 80
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (enemy_width + spacing_x) + enemy_width // 2
                y = start_y + row * (enemy_height + spacing_y) + enemy_height // 2
                
                enemy_img = random.choice(self.enemy_images[self.current_world])
                enemy = Enemy(x, y, enemy_img, self.screen_width, self.current_level)
                self.enemies.add(enemy)
    
    def shoot_player_bullet(self):
        """Player shoots a bullet"""
        if self.player and len(self.player_bullets) < MAX_PLAYER_BULLETS:
            bullet = Bullet(self.player.rect.centerx,
                           self.player.rect.top,
                           self.player_bullet_img,
                           True,
                           self.screen_height)
            self.player_bullets.add(bullet)
    
    def update(self):
        """Update game logic"""
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""
        
        # Update profile screen
        if self.profile_screen.active:
            self.profile_screen.update()
            # Update character selection
            new_char = self.profile_screen.get_selected_character()
            if new_char != self.selected_character:
                self.selected_character = new_char
                self.update_profile_icon()
            return
        
        # Update level selector
        if self.level_selector.active:
            self.level_selector.update()
            return
        
        # Update UI buttons
        mouse_pos = pygame.mouse.get_pos()
        
        if self.state == STATE_MAIN_MENU:
            self.btn_start.update(mouse_pos)
            self.btn_continue.update(mouse_pos)
            self.btn_help.update(mouse_pos)
            self.btn_game.update(mouse_pos)
            self.btn_quit.update(mouse_pos)
            self.popup_help.update(mouse_pos)
            self.popup_game.update(mouse_pos)
        
        elif self.state == STATE_LOGIN:
            self.login_username.update()
            self.login_password.update()
            self.btn_login.update(mouse_pos)
            self.btn_to_register.update(mouse_pos)
            self.btn_guest.update(mouse_pos)
        
        elif self.state == STATE_REGISTER:
            self.register_username.update()
            self.register_email.update()
            self.register_password.update()
            self.register_confirm.update()
            self.btn_register.update(mouse_pos)
            self.btn_back_login.update(mouse_pos)
        
        elif self.state == STATE_GAMEPLAY:
            self.update_gameplay()
        
        elif self.state == STATE_GAME_OVER:
            self.btn_restart.update(mouse_pos)
            self.btn_finish.update(mouse_pos)
        
        elif self.state == STATE_LEVEL_WIN:
            self.btn_next_level.update(mouse_pos)
            self.btn_level_select.update(mouse_pos)
        
        # Update profile icon
        if self.profile_icon:
            self.profile_icon.update(mouse_pos)
    
    def update_gameplay(self):
        """Update gameplay logic"""
        if not self.player:
            return
        
        # Update player
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # Update bullets
        self.player_bullets.update()
        self.enemy_bullets.update()
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update()
            
            # Enemy shooting
            if enemy.can_shoot():
                bullet = Bullet(enemy.rect.centerx,
                               enemy.rect.bottom,
                               self.enemy_bullet_img,
                               False,
                               self.screen_height)
                self.enemy_bullets.add(bullet)
        
        # Update explosions
        self.explosions.update()
        
        # Collision detection
        self.check_collisions()
        
        # Check win condition
        if len(self.enemies) == 0:
            self.state = STATE_LEVEL_WIN
            # Save score
            if self.auth.current_user:
                self.auth.update_user_data(
                    high_score=max(self.current_score, 
                                  self.auth.get_user_data("high_score") or 0)
                )
    
    def check_collisions(self):
        """Check all collisions"""
        # Player bullets hit enemies
        for bullet in self.player_bullets:
            hits = pygame.sprite.spritecollide(bullet, self.enemies, True)
            if hits:
                bullet.kill()
                self.current_score += 10 * self.current_level
                # Create explosion (enemy destroyed)
                for enemy in hits:
                    explosion = Explosion(enemy.rect.centerx, enemy.rect.centery, 
                                        explosion_img=self.enemy_explosion_img)
                    self.explosions.add(explosion)
        
        # Enemy bullets hit player
        if self.player:
            hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            if hits:
                self.lives -= len(hits)
                if self.lives <= 0:
                    # Game over
                    explosion = Explosion(self.player.rect.centerx, 
                                        self.player.rect.centery, RED,
                                        explosion_img=self.player_explosion_img)
                    self.explosions.add(explosion)
                    self.player = None
                    
                    # Save score
                    username = self.auth.current_user or "Guest"
                    if username != "Guest":
                        position, is_top_20 = self.score_manager.add_score(
                            username, self.current_score, self.current_level
                        )
                    
                    self.state = STATE_GAME_OVER
        
        # Enemies reach player (collide with player)
        if self.player:
            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if hits:
                self.lives -= len(hits) * 2  # Lose more lives for direct hits
                if self.lives <= 0:
                    self.player = None
                    self.state = STATE_GAME_OVER
    
    def draw(self):
        """Draw everything"""
        # Draw based on state
        if self.level_selector.active:
            self.level_selector.draw(self.menu_bg)
        elif self.state == STATE_MAIN_MENU:
            self.draw_main_menu()
        elif self.state == STATE_LOGIN:
            self.draw_login()
        elif self.state == STATE_REGISTER:
            self.draw_register()
        elif self.state == STATE_GAMEPLAY:
            self.draw_gameplay()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_LEVEL_WIN:
            self.draw_level_win()
        
        # Draw profile icon (on most screens)
        if (not self.level_selector.active and 
            self.state not in [STATE_LOGIN, STATE_REGISTER]):
            if self.profile_icon:
                self.profile_icon.draw(self.screen)
        
        # Draw profile screen (overlay)
        if self.profile_screen.active:
            self.profile_screen.draw()
        
        # Draw message
        if self.message:
            msg_surf = self.font_small.render(self.message, True, self.message_color)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2, 50))
            # Draw background for readability
            bg_rect = msg_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), bg_rect, border_radius=5)
            self.screen.blit(msg_surf, msg_rect)
        
        pygame.display.flip()
    
    def draw_main_menu(self):
        """Draw main menu"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Title
        title = self.font_large.render("S I 3 L N", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        
        # Title shadow
        shadow = self.font_large.render("S I 3 L N", True, BLACK)
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_small.render("Space Invaders III - Last Night", True, CYAN)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Buttons
        self.btn_start.draw(self.screen)
        self.btn_continue.draw(self.screen)
        self.btn_help.draw(self.screen)
        self.btn_game.draw(self.screen)
        self.btn_quit.draw(self.screen)
        
        # Draw popups on top
        self.popup_help.draw(self.screen)
        self.popup_game.draw(self.screen)
    
    def draw_login(self):
        """Draw login screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("CONNEXION", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Input fields
        self.login_username.draw(self.screen)
        self.login_password.draw(self.screen)
        
        # Buttons
        self.btn_login.draw(self.screen)
        self.btn_to_register.draw(self.screen)
        self.btn_guest.draw(self.screen)
    
    def draw_register(self):
        """Draw register screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("INSCRIPTION", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Input fields
        self.register_username.draw(self.screen)
        self.register_email.draw(self.screen)
        self.register_password.draw(self.screen)
        self.register_confirm.draw(self.screen)
        
        # Buttons
        self.btn_register.draw(self.screen)
        self.btn_back_login.draw(self.screen)
    
    def draw_gameplay(self):
        """Draw gameplay"""
        self.screen.blit(self.game_bg, (0, 0))
        
        # Draw entities
        if self.player:
            self.screen.blit(self.player.image, self.player.rect)
        
        self.enemies.draw(self.screen)
        self.player_bullets.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
        self.explosions.draw(self.screen)
        
        # Draw HUD
        self.draw_hud()
    
    def draw_hud(self):
        """Draw heads-up display"""
        # Background panel
        hud_panel = pygame.Surface((self.screen_width, 50), pygame.SRCALPHA)
        hud_panel.fill((0, 0, 0, 180))
        self.screen.blit(hud_panel, (0, 0))
        
        # Score
        score_text = self.font_small.render(f"Score: {self.current_score}", True, WHITE)
        self.screen.blit(score_text, (20, 15))
        
        # Level
        level_text = self.font_small.render(f"Niveau: {self.current_level}", True, CYAN)
        level_rect = level_text.get_rect(center=(self.screen_width // 2, 25))
        self.screen.blit(level_text, level_rect)
        
        # Lives
        lives_text = self.font_small.render(f"Vies: {self.lives}", True, RED)
        lives_rect = lives_text.get_rect(right=self.screen_width - 120, centery=25)
        self.screen.blit(lives_text, lives_rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title, title_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Score Final: {self.current_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(score_text, score_rect)
        
        level_text = self.font_small.render(f"Niveau atteint: {self.current_level}", True, CYAN)
        level_rect = level_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(level_text, level_rect)
        
        # High scores
        self.draw_high_scores(300)
        
        # Buttons
        self.btn_restart.draw(self.screen)
        self.btn_finish.draw(self.screen)
    
    def draw_high_scores(self, start_y):
        """Draw high scores table"""
        title = self.font_medium.render("MEILLEURS SCORES", True, YELLOW)
        title_rect = title.get_rect(center=(self.screen_width // 2, start_y))
        self.screen.blit(title, title_rect)
        
        scores = self.score_manager.get_top_scores(10)
        
        y = start_y + 50
        for i, entry in enumerate(scores):
            rank_color = YELLOW if i < 3 else WHITE
            text = f"{i+1}. {entry['username'][:15]:15s} - {entry['score']:6d} pts (Niv {entry['level']})"
            score_surf = self.font_tiny.render(text, True, rank_color)
            score_rect = score_surf.get_rect(center=(self.screen_width // 2, y))
            self.screen.blit(score_surf, score_rect)
            y += 25
            
            if y > self.screen_height - 150:
                break
    
    def draw_level_win(self):
        """Draw level win screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render(f"NIVEAU {self.current_level} TERMINÉ!", True, GREEN)
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Score
        score_text = self.font_medium.render(f"Score: {self.current_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(self.screen_width // 2, 280))
        self.screen.blit(score_text, score_rect)
        
        # Buttons
        self.btn_next_level.draw(self.screen)
        self.btn_level_select.draw(self.screen)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.RESIZABLE
            )
        else:
            self.screen = pygame.display.set_mode(
                (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT),
                pygame.RESIZABLE
            )
        
        # Update screen dimensions
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # Recreate UI and reload assets
        self.load_assets()
        self.create_ui()
        self.profile_screen = ProfileScreen(self.screen, self.auth, self.players)
        self.level_selector = LevelSelector(self.screen, WORLDS)
        self.update_profile_icon()
    
    def handle_resize(self, width, height):
        """Handle window resize"""
        self.screen_width = width
        self.screen_height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        # Recreate UI
        self.load_assets()
        self.create_ui()
        self.profile_screen = ProfileScreen(self.screen, self.auth, self.players)
        self.level_selector = LevelSelector(self.screen, WORLDS)
        self.update_profile_icon()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
