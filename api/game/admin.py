from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Player, World, GameSession, Achievement, PlayerAchievement, Leaderboard, PowerUp


# Unregister the default User admin and register with proper password handling
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin that completely hides password hashes
    and provides secure password change interface
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Add readonly fields including custom password display
    readonly_fields = ('last_login', 'date_joined', 'password_display')
    
    def password_display(self, obj):
        """
        Display a secure message instead of password hash
        """
        return format_html(
            '<div style="padding: 10px; background-color: #f8f9fa; border-radius: 4px;">'
            '<strong>🔒 Password is securely hashed and cannot be displayed.</strong><br>'
            '<small>Raw passwords are not stored, so there is no way to see this user\'s password, '
            'but you can change the password using <a href="../password/">this form</a>.</small>'
            '</div>'
        )
    password_display.short_description = 'Password'
    
    # Override fieldsets to use custom password display
    fieldsets = (
        (None, {'fields': ('username', 'password_display')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # For adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    
    # Ensure password is never displayed in forms
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Remove password field from the form entirely when editing
        if obj and 'password' in form.base_fields:
            del form.base_fields['password']
        return form


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'total_score', 'games_played', 'highest_level', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('created_at', 'highest_level')
    ordering = ('-total_score',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Player Info', {'fields': ('username', 'email', 'user')}),
        ('Game Stats', {'fields': ('total_score', 'games_played', 'highest_level')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty_multiplier', 'background_color')
    list_filter = ('name', 'difficulty_multiplier')
    search_fields = ('name', 'description')


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('player', 'world', 'score', 'level_reached', 'completed', 'started_at', 'ended_at')
    list_filter = ('world', 'completed', 'started_at')
    search_fields = ('player__username',)
    ordering = ('-started_at',)
    readonly_fields = ('started_at',)
    
    fieldsets = (
        ('Session Info', {'fields': ('player', 'world', 'completed')}),
        ('Game Stats', {'fields': ('score', 'level_reached', 'enemies_killed', 'bullets_fired', 'accuracy')}),
        ('Timing', {'fields': ('duration_seconds', 'started_at', 'ended_at')}),
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'points', 'rarity', 'requirement_type', 'requirement_value')
    list_filter = ('rarity', 'requirement_type')
    search_fields = ('name', 'description')
    ordering = ('-points',)


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ('player', 'achievement', 'unlocked_at')
    list_filter = ('achievement', 'unlocked_at')
    search_fields = ('player__username', 'achievement__name')
    ordering = ('-unlocked_at',)
    readonly_fields = ('earned_at', 'unlocked_at')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('rank', 'player', 'score', 'period', 'world', 'updated_at')
    list_filter = ('period', 'world', 'created_at')
    search_fields = ('player__username',)
    ordering = ('period', 'rank')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PowerUp)
class PowerUpAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_seconds', 'rarity')
    list_filter = ('name', 'rarity')
    search_fields = ('name', 'description')
