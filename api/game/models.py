from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Player(models.Model):
    """Player profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile', null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    total_score = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    highest_level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_score']

    def __str__(self):
        return self.username


class World(models.Model):
    """Game world/theme model"""
    WORLD_TYPES = [
        ('CLASSIC', 'Classic Space'),
        ('NEON', 'Neon City'),
        ('FOREST', 'Mystic Forest'),
        ('OCEAN', 'Deep Ocean'),
        ('DESERT', 'Mars Desert'),
    ]
    
    name = models.CharField(max_length=50, choices=WORLD_TYPES, unique=True)
    description = models.TextField(blank=True)
    background_color = models.CharField(max_length=7, default='#000000')  # Hex color
    difficulty_multiplier = models.FloatField(default=1.0)
    
    def __str__(self):
        return self.get_name_display()


class GameSession(models.Model):
    """Individual game session model"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sessions')
    world = models.ForeignKey(World, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.IntegerField(default=0)
    level_reached = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    enemies_killed = models.IntegerField(default=0)
    bullets_fired = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    duration_seconds = models.IntegerField(default=0)  # Game duration in seconds
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.player.username} - Level {self.level_reached} - Score {self.score}"

    def calculate_accuracy(self):
        """Calculate shooting accuracy percentage"""
        if self.bullets_fired > 0:
            self.accuracy = (self.enemies_killed / self.bullets_fired) * 100
        else:
            self.accuracy = 0.0
        return self.accuracy


class Leaderboard(models.Model):
    """Leaderboard entry model"""
    PERIOD_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('ALL_TIME', 'All Time'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='leaderboard_entries')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    world = models.ForeignKey(World, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['period', 'rank']
        unique_together = ['player', 'period', 'world']

    def __str__(self):
        return f"#{self.rank} - {self.player.username} ({self.period})"


class Achievement(models.Model):
    """Achievement/Trophy model"""
    RARITY_CHOICES = [
        ('COMMON', 'Common'),
        ('RARE', 'Rare'),
        ('EPIC', 'Epic'),
        ('LEGENDARY', 'Legendary'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)  # Icon identifier
    points = models.IntegerField(default=10)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='COMMON')
    requirement_type = models.CharField(max_length=50)  # e.g., 'score', 'level', 'enemies_killed'
    requirement_value = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name


class PlayerAchievement(models.Model):
    """Track player achievements"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    unlocked_at = models.DateTimeField(auto_now_add=True)  # Alias for compatibility
    
    class Meta:
        unique_together = ['player', 'achievement']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.player.username} - {self.achievement.name}"


class PowerUp(models.Model):
    """Power-up types in the game"""
    POWERUP_TYPES = [
        ('SPEED', 'Speed Boost'),
        ('SHIELD', 'Shield'),
        ('DOUBLE_FIRE', 'Double Fire'),
        ('TRIPLE_FIRE', 'Triple Fire'),
        ('HEALTH', 'Extra Life'),
        ('SCORE_MULTIPLIER', 'Score Multiplier'),
    ]
    
    name = models.CharField(max_length=50, choices=POWERUP_TYPES, unique=True)
    description = models.TextField()
    duration_seconds = models.IntegerField(default=10)
    rarity = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(1)])  # 0-1, drop chance
    
    def __str__(self):
        return self.get_name_display()
