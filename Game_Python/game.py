import asyncio
"""
Main Game class for SI3LN Game
Integrates all screens and game logic
"""
import pygame
import random
import sys
from constants import *
from resolution_manager import ResolutionManager
from utils import load_image, draw_text, load_enemy_images, load_boss_images, create_bullet_surface
from auth import AuthSystem
from scores import ScoreManager
from profile import ProfileScreen
from level_selector import LevelSelector
from entities import Player, Enemy, Bullet, Explosion, Bonus, SpecialAttack
from ui_components import Button, InputField, ProfileIcon, Panel, PopUp
from api_client import api_client  # REST-API integration (scores / sessions)


class Game:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        
        # Screen setup with resizable window
        self.screen_info = pygame.display.Info()
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT
        # Real display surface – only used for the final blit in draw()
        self._display = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.SCALED | pygame.RESIZABLE
        )
        pygame.display.set_caption("S I 3 L N")

        # ResolutionManager: scale factor S = min(W/1280, H/720)
        # rm.canvas is the 1280×720 reference surface; all drawing targets it.
        # rm.present(_display) scales + centres it on the real window each frame.
        self.rm = ResolutionManager(self.screen_width, self.screen_height)
        # self.screen always points to the reference canvas so every existing
        # draw call (self.screen.blit / pygame.draw…) writes to reference space.
        self.screen = self.rm.canvas

        # screen_width / screen_height stay fixed at REF values from here on;
        # actual window size is tracked exclusively in self.rm.
        self.screen_width = REF_WIDTH
        self.screen_height = REF_HEIGHT

        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = STATE_MAIN_MENU
        self.prev_state = None
        
        # Systems
        self.auth = AuthSystem()
        self.score_manager = ScoreManager()

        # ── API integration ───────────────────────────────────────────
        # If a JWT token is available (set by the web dashboard / env
        # variable SI3LN_TOKEN) authenticate the player automatically.
        self.api = api_client
        if self.api.is_authenticated():
            self.auth.current_user = self.api.get_username()
            self.auth.guest_mode   = False
        else:
            self.auth.login_as_guest(0)
        self._session_started = False
        self._session_start_time = 0
        
        # Game data
        self.current_score = 0
        self.current_level = 1
        self.current_world = "Space"
        self.lives = MAX_LIVES
        self.selected_character = 0
        self.enemies_killed = 0
        
        # Nouveaux systèmes
        self.bonuses = pygame.sprite.Group()
        self.active_bonuses = {
            "shield": {"active": False, "timer": 0, "duration": 3000},
            "mega_shot": {"active": False, "timer": 0, "duration": 5000}
        }
        
        self.special_attacks = pygame.sprite.Group()
        self.player_debuffs = {
            "frozen": False,
            "blinded": False, 
            "rooted": False,
            "timer": 0,
            "duration": 0
        }
        
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
        
        # ── Touch / mobile controls (mouse-based – pygbag maps touch→mouse) ─
        self.touch_held = False            # True while mouse/finger is held down
        self.touch_move_pos = None         # (x, y) target while dragging
        self.touch_fire_held = False       # True while fire button is held
        self.touch_auto_fire_timer = 0     # auto-repeat fire cooldown
        self.touch_auto_fire_delay = 300   # ms between auto-fire shots
        # Touch button zones (set in _build_touch_zones)
        self.touch_fire_rect = None
        self.touch_shield_rect = None
        self.touch_mega_rect = None
        self._build_touch_zones()
        
        # Timers pour les attaques spéciales
        self.last_special_attack_time = 0
        self.special_attack_cooldown = 10000  # 10 secondes entre les attaques
    
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
        """Create all UI elements in reference (1280×720) space.

        Portrait mode (rm.is_portrait) stacks elements that would
        otherwise overflow a narrow screen vertically at the bottom-centre
        instead of horizontally in the bottom-right corner.
        """
        cx = self.rm.cx   # 640 – horizontal centre of reference canvas
        cy = self.rm.cy   # 360 – vertical centre of reference canvas

        # Main menu buttons - Style arcade avec fond transparent
        self.btn_start = Button(cx, cy - 40, 250, 70, "START",
                               self.font_medium, bg_color=None, text_color=WHITE, border_color=WHITE)
        self.btn_continue = Button(cx, cy + 50, 250, 70, "PLAY",
                                   self.font_medium, bg_color=None, text_color=WHITE, border_color=WHITE)

        if self.rm.is_portrait:
            # Portrait: stack the three utility buttons vertically at bottom-centre
            self.btn_help = Button(cx, REF_HEIGHT - 175,
                                  150, 50, "AIDE", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
            self.btn_game = Button(cx, REF_HEIGHT - 115,
                                  150, 50, "GAME", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
            self.btn_quit = Button(cx, REF_HEIGHT - 55,
                                  150, 50, "QUITTER", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
        else:
            # Landscape: original bottom-right corner layout
            self.btn_help = Button(REF_WIDTH - 100, REF_HEIGHT - 70,
                                  150, 50, "AIDE", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
            self.btn_game = Button(REF_WIDTH - 100, REF_HEIGHT - 130,
                                  150, 50, "GAME", self.font_small, bg_color=None, text_color=WHITE, border_color=WHITE)
            self.btn_quit = Button(REF_WIDTH - 100, REF_HEIGHT - 190,
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
        
        # Game over buttons – side-by-side in landscape, stacked in portrait
        if self.rm.is_portrait:
            self.btn_restart = Button(cx, REF_HEIGHT - 130,
                                     200, 60, "RESTART", self.font_medium,
                                     bg_color=ORANGE)
            self.btn_finish = Button(cx, REF_HEIGHT - 60,
                                    200, 60, "FINISH", self.font_medium,
                                    bg_color=RED)
        else:
            self.btn_restart = Button(cx - 130, REF_HEIGHT - 80,
                                     200, 60, "RESTART", self.font_medium,
                                     bg_color=ORANGE)
            self.btn_finish = Button(cx + 130, REF_HEIGHT - 80,
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
        
        # Popups
        help_content = [
            "=== CONTROLES ===",
            "",
            "Deplacement: Fleches ou WASD",
            "Tirer: ESPACE",
            "Bouclier: B",
            "Mega Tir: MAJ",
            "Plein ecran: F11",
            "Retour menu: ESC",
            "",
            "Detruisez tous les ennemis!",
            "Evitez leurs tirs!"
        ]
        
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
        
        self.popup_help = PopUp(400, 500, "AIDE", help_content,
                               REF_WIDTH, REF_HEIGHT, self.font_small, self.font_large)
        self.popup_game = PopUp(400, 500, "A PROPOS DU JEU", game_content,
                               REF_WIDTH, REF_HEIGHT, self.font_small, self.font_large)
    
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
    
    def _transform_event(self, event: pygame.event.Event) -> pygame.event.Event:
        """Return a copy of a mouse event with pos in reference (canvas) space.

        MOUSEBUTTONDOWN / UP / MOTION events carry screen-space coordinates.
        Sub-systems (LevelSelector, ProfileScreen) store their rects in
        reference space (1280×720 canvas), so we must remap before dispatch.

        Non-mouse events are returned unchanged.
        """
        if event.type not in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
        ):
            return event
        if not hasattr(event, "pos"):
            return event

        ref_pos = self.rm.screen_to_ref(*event.pos)
        attrs: dict = {"pos": ref_pos}
        for attr in ("button", "buttons", "rel", "touch", "which"):
            if hasattr(event, attr):
                attrs[attr] = getattr(event, attr)
        return pygame.event.Event(event.type, attrs)

    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Handle window resize
            if event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.w, event.h)
            
            # ── Track mouse/touch held state (for drag-to-move) ───────
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.touch_held = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.touch_held = False
                self.touch_move_pos = None
                self.touch_fire_held = False
            elif event.type == pygame.MOUSEMOTION and self.touch_held:
                self.touch_move_pos = event.pos
            
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
                if self.profile_screen.handle_event(self._transform_event(event)):
                    self.update_profile_icon()
                continue

            # Level selector
            if self.level_selector.active:
                result = self.level_selector.handle_event(self._transform_event(event))
                if result:
                    print(f"[DEBUG] Level selector returned: {result}")
                    if result[0] == "START_LEVEL":
                        self.current_world = result[1]
                        self.current_level = result[2]
                        print(f"[DEBUG] Starting world={self.current_world}, level={self.current_level}")
                        self.level_selector.close()
                        self.start_level()
                    elif result[0] == "BACK":
                        self.level_selector.close()
                        self.state = STATE_MAIN_MENU
                continue
            
            # State-specific event handling
            if self.state == STATE_MAIN_MENU:
                self.handle_main_menu_events(event)
            elif self.state in (STATE_LOGIN, STATE_REGISTER):
                # Auth is handled by the web dashboard – redirect to main menu
                self.state = STATE_MAIN_MENU
            elif self.state == STATE_GAMEPLAY:
                self.handle_gameplay_events(event)
            elif self.state == STATE_GAME_OVER:
                self.handle_game_over_events(event)
            elif self.state == STATE_LEVEL_WIN:
                self.handle_level_win_events(event)
    
    def handle_main_menu_events(self, event):
        """Handle main menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.rm.screen_to_ref(*event.pos)
            
            if self.btn_start.is_clicked(pos):
                self.auth.login_as_guest(self.selected_character)
                self.update_profile_icon()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            elif self.btn_continue.is_clicked(pos):
                # Login is handled by the web dashboard – go straight to play
                if self.api.is_authenticated():
                    self.update_profile_icon()
                else:
                    self.auth.login_as_guest(self.selected_character)
                    self.update_profile_icon()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            elif self.btn_help.is_clicked(pos):
                self.popup_help.open()
            
            elif self.btn_game.is_clicked(pos):
                self.popup_game.open()
            
            elif self.btn_quit.is_clicked(pos):
                self.running = False
            
            # Check popup clicks
            if self.popup_help.handle_click(pos) or self.popup_game.handle_click(pos):
                pass
            
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
                    self.auth.login(username, password)
                    self.update_profile_icon()
                    self.state = STATE_MAIN_MENU
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
            
            # Contrôles des bonus
            if event.key == pygame.K_b and self.active_bonuses["shield"]["active"]:
                self.activate_shield()
            
            if event.key == pygame.K_LSHIFT and self.active_bonuses["mega_shot"]["active"]:
                self.mega_shot()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
<<<<<<< HEAD
            pos = event.pos
            
            # On-screen touch buttons (fire / shield / mega)
            if self.touch_fire_rect and self.touch_fire_rect.collidepoint(pos):
                self.touch_fire_held = True
                self.shoot_player_bullet()
                self.touch_auto_fire_timer = pygame.time.get_ticks()
                return  # Don't process as movement
            if self.touch_shield_rect and self.touch_shield_rect.collidepoint(pos):
                if self.active_bonuses["shield"]["active"]:
                    self.activate_shield()
                return
            if self.touch_mega_rect and self.touch_mega_rect.collidepoint(pos):
                if self.active_bonuses["mega_shot"]["active"]:
                    self.mega_shot()
                return
            
            # Start dragging to move
            self.touch_move_pos = pos
            
=======
            pos = self.rm.screen_to_ref(*event.pos)

>>>>>>> 8af4e2f (Implement responsive design with ResolutionManager and update UI components)
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.prev_state = self.state
                self.profile_screen.open()
    
    def handle_game_over_events(self, event):
        """Handle game over screen events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.rm.screen_to_ref(*event.pos)
            
            if self.btn_restart.is_clicked(pos):
                self._end_api_session()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            elif self.btn_finish.is_clicked(pos):
                self._end_api_session()
                self.state = STATE_MAIN_MENU
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.profile_screen.open()
    
    def handle_level_win_events(self, event):
        """Handle level win screen events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = self.rm.screen_to_ref(*event.pos)
            
            if self.btn_next_level.is_clicked(pos):
                self.current_level += 1
                max_levels = WORLDS[self.current_world]["levels"]
                if self.current_level > max_levels:
                    self._end_api_session()
                    self.show_message("Tous les niveaux terminés!", GREEN)
                    self.level_selector.open()
                    self.state = STATE_LEVEL_SELECT
                else:
                    self.start_level()
            
            elif self.btn_level_select.is_clicked(pos):
                self._end_api_session()
                self.level_selector.open()
                self.state = STATE_LEVEL_SELECT
            
            # Profile icon
            if self.profile_icon and self.profile_icon.is_clicked(pos):
                self.profile_screen.open()
    
    def _end_api_session(self):
        """End the current API game session (if any) and reset tracking."""
        if self._session_started and self.api.is_authenticated():
            duration = (pygame.time.get_ticks() - self._session_start_time) // 1000
            self.api.end_session(
                score=self.current_score,
                level=self.current_level,
                enemies_killed=self.enemies_killed,
                duration=duration,
            )
        self._session_started = False
        self._session_start_time = 0

    def trigger_game_over(self):
        """Centralised game-over handler: save score locally and set state."""
        self.player = None
        username = self.auth.current_user or "Guest"
        if username != "Guest":
            self.score_manager.add_score(
                username, self.current_score, self.current_level
            )
            self.auth.update_user_data(
                high_score=max(self.current_score,
                               self.auth.get_user_data("high_score") or 0)
            )
        self.state = STATE_GAME_OVER

    def start_level(self):
        """Start a new level"""
        # Open (or re-use) an API game session
        if self.api.is_authenticated() and not self._session_started:
            from constants import WORLD_IDS
            world_id = WORLD_IDS.get(self.current_world, 1)
            self.api.start_session(world_id=world_id)
            self._session_started = True
            self._session_start_time = pygame.time.get_ticks()
            self.enemies_killed = 0
        print(f"[DEBUG] Starting level {self.current_level} in world {self.current_world}")
        self.state = STATE_GAMEPLAY
        self.lives = MAX_LIVES
        
        # Set the background for the current world
        self.game_bg = self.world_backgrounds.get(self.current_world, self.world_backgrounds["Space"])
        print(f"[DEBUG] Background set for world: {self.current_world}")
        
        # Create bullets with world-specific colors
        if self.current_world in WORLDS and "bullet_colors" in WORLDS[self.current_world]:
            colors = WORLDS[self.current_world]["bullet_colors"]
            
            self.player_bullet_img = create_bullet_surface(
                colors["player"][0], 
                colors["player"][1], 
                (15, 25)
            )
            
            self.enemy_bullet_img = create_bullet_surface(
                colors["enemy"][0], 
                colors["enemy"][1], 
                (10, 20)
            )
            
            print(f"[DEBUG] Bullets created with colors for {self.current_world}")
        
        # Load explosion images specific to the world
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
        self.bonuses.empty()
        self.special_attacks.empty()
        
        # Reset debuffs
        self.player_debuffs = {
            "frozen": False,
            "blinded": False, 
            "rooted": False,
            "timer": 0,
            "duration": 0
        }
        
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
        base_rows = 3
        base_cols = 5
        rows = min(base_rows + self.current_level // 2, 6)
        cols = min(base_cols + self.current_level // 2, 9)
        
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
    
    def activate_shield(self):
        """Active le bouclier du joueur"""
        if self.active_bonuses["shield"]["active"]:
            self.active_bonuses["shield"]["active"] = False
            self.show_message("Bouclier activé!", BLUE)
            # Ici tu peux ajouter un effet visuel de bouclier
    
    def mega_shot(self):
        """Tir spécial plus puissant"""
        if self.active_bonuses["mega_shot"]["active"]:
            # Tir triple
            for i in range(-1, 2):
                bullet = Bullet(self.player.rect.centerx + i*20,
                               self.player.rect.top,
                               self.player_bullet_img,
                               True,
                               self.screen_height)
                self.player_bullets.add(bullet)
            self.active_bonuses["mega_shot"]["active"] = False
            self.show_message("Mega tir activé!", YELLOW)
    
    def spawn_bonus(self, x, y):
        """Fait tomber un bonus aléatoire"""
        bonus_type = random.choice(["life", "shield", "mega_shot"])
        bonus = Bonus(x, y, bonus_type)
        self.bonuses.add(bonus)
    
    def activate_bonus(self, bonus_type):
        """Active un bonus"""
        if bonus_type == "life":
            self.lives = min(self.lives + 1, 10)
            self.show_message("+1 Vie!", GREEN)
        else:
            self.active_bonuses[bonus_type]["active"] = True
            self.active_bonuses[bonus_type]["timer"] = pygame.time.get_ticks()
            self.show_message(f"{bonus_type.title()} activé!", BLUE if bonus_type == "shield" else YELLOW)
    
    def trigger_world_special(self):
        """Déclenche une attaque spéciale selon le monde"""
        world = self.current_world
        
        if world == "Space":
            self.spawn_space_lasers()
        elif world == "Desert":
            self.blind_player()
        elif world == "Forest": 
            self.root_player()
        elif world == "Marine":
            self.spawn_ice_ball()
        elif world == "Apocalyptic":
            self.spawn_energy_ball()
    
    def spawn_space_lasers(self):
        """1-3 rayons laser tombent au hasard"""
        num_lasers = random.randint(1, min(3, self.current_level))
        for _ in range(num_lasers):
            attack = SpecialAttack("laser", "Space", self.current_level, 
                                 self.screen_width, self.screen_height)
            self.special_attacks.add(attack)
        self.show_message("Rayons laser!", PURPLE)
    
    def spawn_ice_ball(self):
        """Balle de glace qui gèle les tirs"""
        attack = SpecialAttack("ice", "Marine", self.current_level,
                              self.screen_width, self.screen_height)
        self.special_attacks.add(attack)
        self.show_message("Balle de glace!", LIGHT_BLUE)
    
    def spawn_energy_ball(self):
        """Boule d'énergie qui rebondit"""
        attack = SpecialAttack("energy", "Apocalyptic", self.current_level,
                              self.screen_width, self.screen_height)
        self.special_attacks.add(attack)
        self.show_message("Boule d'énergie!", YELLOW)
    
    def blind_player(self):
        """Nuage de sable - joueur ne voit rien"""
        attack = SpecialAttack("sand", "Desert", self.current_level,
                              self.screen_width, self.screen_height)
        self.special_attacks.add(attack)
        self.player_debuffs["blinded"] = True
        self.player_debuffs["timer"] = pygame.time.get_ticks()
        self.player_debuffs["duration"] = min(1000 + (self.current_level * 200), 3000)
        self.show_message("Nuage de sable!", SAND_COLOR)
    
    def root_player(self):
        """Racines - joueur ne peut plus bouger"""
        attack = SpecialAttack("roots", "Forest", self.current_level,
                              self.screen_width, self.screen_height)
        self.special_attacks.add(attack)
        self.player_debuffs["rooted"] = True
        self.player_debuffs["timer"] = pygame.time.get_ticks()
        self.player_debuffs["duration"] = min(1500 + (self.current_level * 150), 3500)
        self.show_message("Racines!", BROWN)
    
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
            new_char = self.profile_screen.get_selected_character()
            if new_char != self.selected_character:
                self.selected_character = new_char
                self.update_profile_icon()
            return
        
        # Update level selector (pass reference-space mouse pos for hover)
        if self.level_selector.active:
            self.level_selector.update(self.rm.screen_to_ref(*pygame.mouse.get_pos()))
            return
        
        # Transform current mouse position to reference (canvas) space so
        # all hover/update calls receive coordinates that match the UI rects.
        mouse_pos = self.rm.screen_to_ref(*pygame.mouse.get_pos())
        
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
        
        # Update player (sauf si rooté)
        keys = pygame.key.get_pressed()
        if not self.player_debuffs["rooted"]:
            # Keyboard movement
            self.player.update(keys)
            # Touch/mouse drag movement — move player toward held position
            if self.touch_held and self.touch_move_pos and not self.touch_fire_held:
                self.player.move_toward(*self.touch_move_pos)
        
        # Touch auto-fire: if fire button is held, keep shooting
        if self.touch_fire_held:
            now = pygame.time.get_ticks()
            if now - self.touch_auto_fire_timer >= self.touch_auto_fire_delay:
                self.shoot_player_bullet()
                self.touch_auto_fire_timer = now
        
        # Update bullets
        self.player_bullets.update()
        self.enemy_bullets.update()
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update()
            
            # Enemy shooting
            current_time = pygame.time.get_ticks()
            if enemy.can_shoot() and random.random() < enemy.shoot_chance:
                bullet = Bullet(enemy.rect.centerx,
                            enemy.rect.bottom,
                            self.enemy_bullet_img,
                            False,
                            self.screen_height)
                self.enemy_bullets.add(bullet)
                enemy.last_shot = current_time
        
        # Update explosions
        self.explosions.update()
        
        # Update bonuses
        self.bonuses.update()
        
        # Update special attacks
        self.special_attacks.update()
        
        # Gestion des debuffs
        self.update_debuffs()
        
        # Chance de spawner un bonus
        if random.random() < 0.001:  # 0.1% de chance par frame
            x = random.randint(50, self.screen_width - 50)
            self.spawn_bonus(x, 0)
        
        # Chance de déclencher une attaque spéciale
        current_time = pygame.time.get_ticks()
        if (current_time - self.last_special_attack_time > self.special_attack_cooldown and 
            random.random() < 0.01):  # 1% de chance quand le cooldown est écoulé
            self.trigger_world_special()
            self.last_special_attack_time = current_time
        
        # Collision detection
        self.check_collisions()
        
        # Check win condition
        if len(self.enemies) == 0:
            self.state = STATE_LEVEL_WIN
            if self.auth.current_user:
                self.auth.update_user_data(
                    high_score=max(self.current_score, 
                                  self.auth.get_user_data("high_score") or 0)
                )
    
    def update_debuffs(self):
        """Gère la durée des debuffs"""
        current_time = pygame.time.get_ticks()
        
        if self.player_debuffs["blinded"]:
            if current_time - self.player_debuffs["timer"] > self.player_debuffs["duration"]:
                self.player_debuffs["blinded"] = False
        
        if self.player_debuffs["rooted"]:
            if current_time - self.player_debuffs["timer"] > self.player_debuffs["duration"]:
                self.player_debuffs["rooted"] = False
    
    def check_collisions(self):
        """Check all collisions"""
        # Player bullets hit enemies
        for bullet in self.player_bullets:
            hits = pygame.sprite.spritecollide(bullet, self.enemies, True)
            if hits:
                bullet.kill()
                self.enemies_killed += len(hits)
                self.current_score += 10 * self.current_level
                for enemy in hits:
                    explosion = Explosion(enemy.rect.centerx, enemy.rect.centery, 
                                        explosion_img=self.enemy_explosion_img)
                    self.explosions.add(explosion)
                    # Chance de faire tomber un bonus
                    if random.random() < 0.2:  # 20% de chance
                        self.spawn_bonus(enemy.rect.centerx, enemy.rect.centery)
        
        # Enemy bullets hit player
        if self.player:
            hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            if hits:
                self.lives -= len(hits)
                if self.lives <= 0:
                    explosion = Explosion(self.player.rect.centerx, 
                                        self.player.rect.centery, RED,
                                        explosion_img=self.player_explosion_img)
                    self.explosions.add(explosion)
                    self.trigger_game_over()
        
        # Enemies reach player
        if self.player:
            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if hits:
                self.lives -= len(hits) * 2
                if self.lives <= 0:
                    self.trigger_game_over()
        
        # Player collects bonuses
        if self.player:
            collected_bonuses = pygame.sprite.spritecollide(self.player, self.bonuses, True)
            for bonus in collected_bonuses:
                self.activate_bonus(bonus.bonus_type)
        
        # Special attacks hit player
        if self.player:
            for attack in self.special_attacks:
                if pygame.sprite.collide_rect(self.player, attack):
                    if attack.world == "Space":
                        self.lives -= attack.damage
                        attack.kill()
                        if self.lives <= 0:
                            self.trigger_game_over()
    
    def draw(self):
        """Draw everything"""
        # Draw based on state
        if self.level_selector.active:
            self.level_selector.draw(self.menu_bg)
        elif self.state == STATE_MAIN_MENU:
            self.draw_main_menu()
        elif self.state in (STATE_LOGIN, STATE_REGISTER):
            # Auth is handled by the web dashboard – fall back to main menu
            self.state = STATE_MAIN_MENU
            self.draw_main_menu()
        elif self.state == STATE_GAMEPLAY:
            self.draw_gameplay()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        elif self.state == STATE_LEVEL_WIN:
            self.draw_level_win()
        
        # Draw profile icon
        if (not self.level_selector.active and 
            self.state not in [STATE_LOGIN, STATE_REGISTER]):
            if self.profile_icon:
                self.profile_icon.draw(self.screen)
        
        # Draw profile screen
        if self.profile_screen.active:
            self.profile_screen.draw()
        
        # Draw message
        if self.message:
            msg_surf = self.font_small.render(self.message, True, self.message_color)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2, 50))
            bg_rect = msg_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), bg_rect, border_radius=5)
            self.screen.blit(msg_surf, msg_rect)
        
        # Scale the reference canvas to the real window (letterboxing) and flip
        self.rm.present(self._display)
        pygame.display.flip()
    
    def draw_main_menu(self):
        """Draw main menu"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        title = self.font_large.render("S I 3 L N", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        
        shadow = self.font_large.render("S I 3 L N", True, BLACK)
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("Space Invaders III - Last Night", True, CYAN)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        self.btn_start.draw(self.screen)
        self.btn_continue.draw(self.screen)
        self.btn_help.draw(self.screen)
        self.btn_game.draw(self.screen)
        self.btn_quit.draw(self.screen)
        
        self.popup_help.draw(self.screen)
        self.popup_game.draw(self.screen)
    
    def draw_login(self):
        """Draw login screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("CONNEXION", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title, title_rect)
        
        self.login_username.draw(self.screen)
        self.login_password.draw(self.screen)
        
        self.btn_login.draw(self.screen)
        self.btn_to_register.draw(self.screen)
        self.btn_guest.draw(self.screen)
    
    def draw_register(self):
        """Draw register screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("INSCRIPTION", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title, title_rect)
        
        self.register_username.draw(self.screen)
        self.register_email.draw(self.screen)
        self.register_password.draw(self.screen)
        self.register_confirm.draw(self.screen)
        
        self.btn_register.draw(self.screen)
        self.btn_back_login.draw(self.screen)
    
    def draw_gameplay(self):
        self.screen.blit(self.game_bg, (0, 0))
        
        if self.player:
            self.screen.blit(self.player.image, self.player.rect)
        
        self.enemies.draw(self.screen)
        self.player_bullets.draw(self.screen)
        self.enemy_bullets.draw(self.screen)
        self.explosions.draw(self.screen)
        self.bonuses.draw(self.screen)
        self.special_attacks.draw(self.screen)
        
        if self.player_debuffs["blinded"]:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((210, 180, 140, 150))
            self.screen.blit(overlay, (0, 0))
        
        self.draw_hud()
          
        # Draw on-screen touch buttons
        self.draw_touch_controls()
        """Draw heads-up display"""
        hud_panel = pygame.Surface((self.screen_width, 50), pygame.SRCALPHA)
        hud_panel.fill((0, 0, 0, 180))
        self.screen.blit(hud_panel, (0, 0))
        
        score_text = self.font_small.render(f"Score: {self.current_score}", True, WHITE)
        self.screen.blit(score_text, (20, 15))
        
        level_text = self.font_small.render(f"Niveau: {self.current_level}", True, CYAN)
        level_rect = level_text.get_rect(center=(self.screen_width // 2, 25))
        self.screen.blit(level_text, level_rect)
        
        lives_text = self.font_small.render(f"Vies: {self.lives}", True, RED)
        lives_rect = lives_text.get_rect(right=self.screen_width - 120, centery=25)
        self.screen.blit(lives_text, lives_rect)
        
        # Afficher les bonus actifs
        bonus_x = self.screen_width - 250
        if self.active_bonuses["shield"]["active"]:
            shield_text = self.font_tiny.render("BOUCLIER", True, BLUE)
            self.screen.blit(shield_text, (bonus_x, 15))
            bonus_x += 80
        
        if self.active_bonuses["mega_shot"]["active"]:
            mega_text = self.font_tiny.render("MEGA TIR", True, YELLOW)
            self.screen.blit(mega_text, (bonus_x, 15))
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.blit(self.menu_bg, (0, 0))
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title, title_rect)
        
        score_text = self.font_medium.render(f"Score Final: {self.current_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(score_text, score_rect)
        
        level_text = self.font_small.render(f"Niveau atteint: {self.current_level}", True, CYAN)
        level_rect = level_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(level_text, level_rect)
        
        self.draw_high_scores(300)
        
        self.btn_restart.draw(self.screen)
        self.btn_finish.draw(self.screen)
    
    def draw_high_scores(self, start_y):
        """Draw high scores table"""
        title = self.font_medium.render("MEILLEURS SCORES", True, YELLOW)
        title_rect = title.get_rect(center=(self.screen_width // 2, start_y))
        self.screen.blit(title, title_rect)
        
        scores = self.score_manager.get_top_scores(10)
        # Supplement with API leaderboard if local scores are empty
        if not scores:
            try:
                api_lb = self.api.get_leaderboard(limit=10)
                scores = [
                    {"username": e.get("player_username", "?"),
                     "score":    e.get("score", 0),
                     "level":    e.get("level_reached", 1)}
                    for e in api_lb
                ]
            except Exception:
                pass
        
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
        
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render(f"NIVEAU {self.current_level} TERMINÉ!", True, GREEN)
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title, title_rect)
        
        score_text = self.font_medium.render(f"Score: {self.current_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(self.screen_width // 2, 280))
        self.screen.blit(score_text, score_rect)
        
        self.btn_next_level.draw(self.screen)
        self.btn_level_select.draw(self.screen)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode.

        Only the real display (_display) changes.  The reference canvas
        (self.screen) stays at 1280×720 – rm.present() handles the scaling.
        """
        self.is_fullscreen = not self.is_fullscreen

        if self.is_fullscreen:
<<<<<<< HEAD
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED | pygame.RESIZABLE
=======
            self._display = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.RESIZABLE
>>>>>>> 8af4e2f (Implement responsive design with ResolutionManager and update UI components)
            )
        else:
            self._display = pygame.display.set_mode(
                (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT),
                pygame.SCALED | pygame.RESIZABLE
            )

        self.rm.update(self._display.get_width(), self._display.get_height())
        self.create_ui()
        self.update_profile_icon()
        self._build_touch_zones()
    
    def handle_resize(self, width, height):
        """Handle window resize.

        The reference canvas (self.screen, 1280×720) never changes size.
        We only update the real display surface and the ResolutionManager
        so that rm.present() uses the new scale factor and letterbox offsets.
        UI elements are rebuilt when the orientation (portrait ↔ landscape)
        changes to keep layouts appropriate for the new aspect ratio.
        """
        old_portrait = self.rm.is_portrait
        self._display = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.rm.update(width, height)

        if old_portrait != self.rm.is_portrait:
            # Orientation flipped – rebuild layout so portrait/landscape
            # button arrangements match the new screen shape.
            self.create_ui()
            self.update_profile_icon()
    
    async def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            await asyncio.sleep(0)  # yield to browser – rAF controls timing
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
