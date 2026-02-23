from django.contrib import admin
from .models import Player, World, GameSession, Achievement, PlayerAchievement, Leaderboard, PowerUp


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'total_score', 'games_played', 'highest_level', 'created_at')
    search_fields = ('username',)
    list_filter = ('created_at',)
    ordering = ('-total_score',)


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty_multiplier', 'background_color')
    list_filter = ('name',)


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('player', 'world', 'score', 'level_reached', 'started_at', 'ended_at')
    list_filter = ('world', 'started_at')
    search_fields = ('player__username',)
    ordering = ('-started_at',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'points', 'rarity')
    list_filter = ('rarity',)
    search_fields = ('name',)


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ('player', 'achievement', 'unlocked_at')
    list_filter = ('achievement', 'unlocked_at')
    search_fields = ('player__username', 'achievement__name')
    ordering = ('-unlocked_at',)


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('rank', 'player', 'score', 'period', 'world', 'updated_at')
    list_filter = ('period', 'world')
    search_fields = ('player__username',)
    ordering = ('period', 'rank')


@admin.register(PowerUp)
class PowerUpAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_seconds', 'rarity')
    list_filter = ('name',)
    search_fields = ('name',)
