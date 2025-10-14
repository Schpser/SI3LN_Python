import pygame
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else '.'

class Game:
    def __init__(self):
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("S I 3 LN")
        self.clock = pygame.time.Clock()
        
        self.state = "MAIN_MENU"
        self.selected_player = 0
        self.level = 1
        self.score = 0
        self.lives = 5
        
        self.load_assets()
        self.create_buttons()
        
        self.player = None
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

    def load_assets(self):
        # Helper function to get absolute asset path
        def get_asset_path(relative_path):
            return os.path.join(BASE_DIR, relative_path)

        # 1. CORRECTION CRITIQUE DE LA POLICE pour compatibilité web
        # Utiliser pygame.font.Font(None, taille) pour la police Pygame par défaut
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 20)
        
        # Images
        try:
            self.menu_bg = pygame.image.load(get_asset_path("assets/worlds/home_page.jpg")).convert()
            self.menu_bg = pygame.transform.scale(self.menu_bg, (self.screen_width, self.screen_height))
        except Exception as e:
            # print(f"Erreur chargement menu_bg: {e}")
            self.menu_bg = pygame.Surface((self.screen_width, self.screen_height))
            self.menu_bg.fill((0, 0, 100))
        
        try:
            self.game_bg = pygame.image.load(get_asset_path("assets/worlds/background_frozen.jpg")).convert()
            self.game_bg = pygame.transform.scale(self.game_bg, (self.screen_width, self.screen_height))
        except Exception as e:
            # print(f"Erreur chargement game_bg: {e}")
            self.game_bg = pygame.Surface((self.screen_width, self.screen_height))
            self.game_bg.fill((0, 50, 100))
        
        # Players
        self.players = []
        player_files = [
            "1000055338.png", "1000055339.png", "1000055340.png", 
            "1000055341.png", "1000055342.png", "1000055343.png", "1000055344.png"
        ]
        
        for file in player_files:
            try:
                img = pygame.image.load(get_asset_path(f"assets/players/{file}")).convert_alpha()
                img = pygame.transform.scale(img, (100, 100))
                self.players.append(img)
            except Exception as e:
                # print(f"Could not load player: {file}. Error: {e}") 
                surf = pygame.Surface((100, 100))
                surf.set_colorkey((0,0,0))
                color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
                surf.fill(color)
                self.players.append(surf)
        
        # Bullets
        try:
            self.player_bullet_img = pygame.image.load(get_asset_path("assets/sprites/player/player_bullet.png")).convert_alpha()
            self.player_bullet_img = pygame.transform.scale(self.player_bullet_img, (15, 25))
        except Exception as e:
            # print(f"Erreur chargement player_bullet: {e}")
            self.player_bullet_img = pygame.Surface((15, 25))
            self.player_bullet_img.fill((0, 255, 0))
        
        try:
            self.enemy_bullet_img = pygame.image.load(get_asset_path("assets/sprites/ennemy/enemy_bullet.png")).convert_alpha()
            self.enemy_bullet_img = pygame.transform.scale(self.enemy_bullet_img, (10, 20))
        except Exception as e:
            # print(f"Erreur chargement enemy_bullet: {e}")
            self.enemy_bullet_img = pygame.Surface((10, 20))
            self.enemy_bullet_img.fill((255, 0, 0))
        
        # Enemies - Utilisation de noms de fichiers sans caractères spéciaux pour la stabilité web
        self.enemy_images = []
        # ASSUMPTION: Tu as renommé tes fichiers de enemy (1).png à enemy_1.png
        enemy_files = [f"enemy_{i}.png" for i in range(1, 6)]
        
        for file in enemy_files:
            try:
                img = pygame.image.load(get_asset_path(f"assets/enemies/Space_world/{file}")).convert_alpha()
                img = pygame.transform.scale(img, (60, 60))
                self.enemy_images.append(img)
            except Exception as e:
                # print(f"Could not load enemy: {file}. Error: {e}")
                surf = pygame.Surface((60, 60))
                surf.fill((255, 100, 100))
                self.enemy_images.append(surf)
                
    def create_buttons(self):
        self.start_btn = Button(self.screen_width//2, 400, 200, 60, "START", self.font_medium)
        self.continue_btn = Button(self.screen_width//2, 400, 200, 60, "CONTINUE", self.font_medium)
        self.restart_btn = Button(self.screen_width//2, 500, 200, 60, "RESTART", self.font_medium)
        
        self.player_btns = []
        # Correction pour décaler les boutons du centre vers la gauche (selon demande précédente)
        positions = [
            (100, 200), (300, 200), (500, 200), 
            (100, 350), (300, 350), (500, 350), 
            (300, 500) 
        ]
        
        for i, pos in enumerate(positions[:7]):
            self.player_btns.append(Button(pos[0], pos[1], 100, 100, f"P{i+1}", self.font_small))
        
        self.start_game_btn = Button(300, 600, 200, 60, "PLAY", self.font_medium) # Décalé

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.state == "GAMEPLAY":
                    self.shoot_player_bullet()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if self.state == "MAIN_MENU":
                    if self.start_btn.is_clicked(pos):
                        self.state = "PLAYER_SELECT"
                
                elif self.state == "PLAYER_SELECT":
                    for i, btn in enumerate(self.player_btns):
                        if btn.is_clicked(pos):
                            self.selected_player = i
                    if self.start_game_btn.is_clicked(pos):
                        self.start_level()
                
                elif self.state == "LEVEL_WIN":
                    if self.continue_btn.is_clicked(pos):
                        self.level += 1
                        self.start_level()
                
                elif self.state == "GAME_OVER":
                    if self.restart_btn.is_clicked(pos):
                        self.level = 1
                        self.score = 0
                        self.lives = 5
                        self.start_level()
        
        return True

    def start_level(self):
        self.state = "GAMEPLAY"
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        
        player_img = self.players[self.selected_player] if self.selected_player < len(self.players) else self.players[0]
        self.player = Player(self.screen_width//2 - 40, self.screen_height - 150, player_img)
        
        rows = min(2 + self.level, 5)
        cols = min(4 + self.level, 8)
        
        for row in range(rows):
            for col in range(cols):
                x = 100 + col * 80
                y = 50 + row * 80
                enemy_img = random.choice(self.enemy_images)
                enemy = Enemy(x, y, enemy_img)
                self.enemies.add(enemy)

    def shoot_player_bullet(self):
        if self.player and len(self.player_bullets) < 3:
            bullet = Bullet(self.player.rect.centerx - 7, self.player.rect.top, self.player_bullet_img, True)
            self.player_bullets.add(bullet)

    def update(self):
        if self.state == "GAMEPLAY":
            keys = pygame.key.get_pressed()
            if self.player:
                if keys[pygame.K_LEFT] and self.player.rect.left > 0:
                    self.player.rect.x -= 8
                if keys[pygame.K_RIGHT] and self.player.rect.right < self.screen_width:
                    self.player.rect.x += 8
            
            self.player_bullets.update()
            self.enemy_bullets.update()
            
            # Gestion des tirs ennemis
            current_time = pygame.time.get_ticks()
            for enemy in self.enemies:
                enemy.update(self.screen_width)
                
                # Ajout d'une limite pour éviter un tir massif à haut niveau
                if current_time - enemy.last_shot > (2000 - self.level * 100) and random.random() < 0.02 * self.level:
                    bullet = Bullet(enemy.rect.centerx - 5, enemy.rect.bottom, self.enemy_bullet_img, False)
                    self.enemy_bullets.add(bullet)
                    enemy.last_shot = current_time
            
            # Collisions joueur / ennemis
            for bullet in self.player_bullets:
                hits = pygame.sprite.spritecollide(bullet, self.enemies, True)
                for enemy in hits:
                    bullet.kill()
                    self.score += 10
            
            # Collisions ennemi / joueur
            for bullet in self.enemy_bullets:
                if self.player and bullet.rect.colliderect(self.player.rect):
                    bullet.kill()
                    self.lives -= 1
                    if self.lives <= 0:
                        self.player = None 
                        self.state = "GAME_OVER"
            
            if len(self.enemies) == 0:
                self.state = "LEVEL_WIN"

    def draw(self):
        self.screen.fill((0, 0, 0))
        
        if self.state == "MAIN_MENU":
            self.screen.blit(self.menu_bg, (0, 0))
            title = self.font_large.render("S I 3 LN", True, (255, 255, 255))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
            self.start_btn.draw(self.screen)
        
        elif self.state == "PLAYER_SELECT":
            self.screen.blit(self.menu_bg, (0, 0))
            title = self.font_large.render("CHOOSE YOUR HERO", True, (255, 255, 255))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 50))
            
            for i, (btn, img) in enumerate(zip(self.player_btns, self.players[:7])):
                btn.draw(self.screen)
                self.screen.blit(img, (btn.rect.x, btn.rect.y))
                if i == self.selected_player:
                    pygame.draw.rect(self.screen, (255, 255, 0), btn.rect, 3)
            
            self.start_game_btn.draw(self.screen)
        
        elif self.state == "GAMEPLAY":
            self.screen.blit(self.game_bg, (0, 0))
            if self.player:
                self.screen.blit(self.player.image, self.player.rect)
            self.player_bullets.draw(self.screen)
            self.enemy_bullets.draw(self.screen)
            self.enemies.draw(self.screen)
            
            # Correction pour mettre les vies à droite
            score_text = self.font_small.render(f"SCORE: {self.score}  LEVEL: {self.level}  LIVES: {self.lives}", True, (255, 255, 255))
            text_x = self.screen_width - score_text.get_width() - 20 
            self.screen.blit(score_text, (text_x, 20))
        
        elif self.state == "LEVEL_WIN":
            self.screen.blit(self.menu_bg, (0, 0))
            title = self.font_large.render(f"LEVEL {self.level} COMPLETE!", True, (0, 255, 0))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
            self.continue_btn.draw(self.screen)
        
        elif self.state == "GAME_OVER":
            self.screen.blit(self.menu_bg, (0, 0))
            title = self.font_large.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
            score_text = self.font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_text, (self.screen_width//2 - score_text.get_width()//2, 200))
            self.restart_btn.draw(self.screen)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            if self.state != "MAIN_MENU" and self.state != "PLAYER_SELECT":
                self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x - w//2, y - h//2, w, h)
        self.text = text
        self.font = font
    
    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=10)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 1
        self.direction = 1
        self.last_shot = pygame.time.get_ticks()
    
    def update(self, screen_width):
        self.rect.x += self.speed * self.direction
        if self.rect.right >= screen_width or self.rect.left <= 0:
            self.direction *= -1
            self.rect.y += 30
    
    def can_shoot(self):
        return True 

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, image, is_player):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10 if is_player else 5
        self.is_player = is_player
    
    def update(self):
        self.rect.y -= self.speed if self.is_player else -self.speed
        if self.rect.bottom < 0 or self.rect.top > 768:
            self.kill()
