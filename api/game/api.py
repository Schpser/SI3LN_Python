from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from .models import Player, GameSession
from .schemas import (
    PlayerSchema,
    PlayerCreateSchema,
    GameSessionSchema,
    GameSessionCreateSchema,
    GameSessionUpdateSchema,
    LeaderboardEntrySchema,
    MessageSchema,
    WorldSchema,
    AchievementSchema,
    PlayerAchievementSchema,
    EnhancedProfileSchema,
    ProfileUpdateSchema,
)
from .auth.auth_decorators import jwt_auth

router = Router()


# Player endpoints (protected)
@router.get("/players", response=List[PlayerSchema], tags=["Players"], auth=jwt_auth)
def list_players(request):
    """Get all players (requires authentication)"""
    return Player.objects.all()


@router.post("/players", response=PlayerSchema, tags=["Players"])
def create_player(request, payload: PlayerCreateSchema):
    """Create a new player (public for game registration)"""
    player = Player.objects.create(**payload.dict())
    return player


@router.get("/players/{player_id}", response=PlayerSchema, tags=["Players"], auth=jwt_auth)
def get_player(request, player_id: int):
    """Get a specific player by ID (requires authentication)"""
    return get_object_or_404(Player, id=player_id)


@router.put("/players/{player_id}", response=PlayerSchema, tags=["Players"], auth=jwt_auth)
def update_player(request, player_id: int, payload: PlayerCreateSchema):
    """Update a player (requires authentication)"""
    player = get_object_or_404(Player, id=player_id)
    for attr, value in payload.dict().items():
        setattr(player, attr, value)
    player.save()
    return player


@router.delete("/players/{player_id}", response=MessageSchema, tags=["Players"], auth=jwt_auth)
def delete_player(request, player_id: int):
    """Delete a player (requires authentication)"""
    player = get_object_or_404(Player, id=player_id)
    player.delete()
    return {"message": "Player deleted successfully"}


# Game Session endpoints (protected)
@router.get("/sessions", response=List[GameSessionSchema], tags=["Game Sessions"], auth=jwt_auth)
def list_sessions(request, player_id: int = None, world_id: int = None):
    """Get all game sessions (requires authentication)"""
    sessions = GameSession.objects.all()
    if player_id:
        sessions = sessions.filter(player_id=player_id)
    if world_id:
        sessions = sessions.filter(world_id=world_id)
    return sessions.order_by("-started_at")


@router.post("/sessions", response=GameSessionSchema, tags=["Game Sessions"], auth=jwt_auth)
def create_session(request, payload: GameSessionCreateSchema):
    """Create a new game session (requires authentication)"""
    # Validate player exists
    player = Player.objects.filter(id=payload.player_id).first()
    if player is None:
        from ninja.responses import Response
        return Response({"error": f"Player with id {payload.player_id} does not exist."}, status=404)
    session = GameSession.objects.create(**payload.dict())
    return session


@router.get("/sessions/{session_id}", response=GameSessionSchema, tags=["Game Sessions"], auth=jwt_auth)
def get_session(request, session_id: int):
    """Get a specific game session (requires authentication)"""
    return get_object_or_404(GameSession, id=session_id)


@router.patch("/sessions/{session_id}", response=GameSessionSchema, tags=["Game Sessions"], auth=jwt_auth)
def update_session(request, session_id: int, payload: GameSessionUpdateSchema):
    """Update a game session (requires authentication)"""
    from django.utils import timezone
    session = get_object_or_404(GameSession, id=session_id)
    
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(session, attr, value)
    
    # Auto-set ended_at when session is marked completed
    if payload.completed and not session.ended_at:
        session.ended_at = timezone.now()
    
    session.save()
    
    # Update player stats only when the session ends (completed=True)
    if payload.completed and payload.score is not None:
        player = session.player
        player.total_score += payload.score
        player.games_played += 1
        if payload.level_reached is not None and payload.level_reached > player.highest_level:
            player.highest_level = payload.level_reached
        player.save()
    
    return session


@router.delete("/sessions/{session_id}", response=MessageSchema, tags=["Game Sessions"], auth=jwt_auth)
def delete_session(request, session_id: int):
    """Delete a game session (requires authentication)"""
    session = get_object_or_404(GameSession, id=session_id)
    session.delete()
    return {"message": "Session deleted successfully"}


# Leaderboard endpoints (public - no auth required for viewing)
@router.get("/leaderboard", response=List[LeaderboardEntrySchema], tags=["Leaderboard"])
def get_leaderboard(request, world_id: int = None, limit: int = 10):
    """Get the leaderboard (public access)"""
    sessions = GameSession.objects.select_related("player", "world")
    
    if world_id:
        sessions = sessions.filter(world_id=world_id)
    
    sessions = sessions.order_by("-score")[:limit]
    
    leaderboard = []
    for rank, session in enumerate(sessions, start=1):
        leaderboard.append({
            "rank": rank,
            "player_id": session.player.id,
            "player_username": session.player.username,
            "score": session.score,
            "level_reached": session.level_reached,
            "world_name": session.world.name if session.world else None,
            "created_at": session.started_at,
        })
    
    return leaderboard


# Stats endpoint (public - no auth required)
@router.get("/stats", tags=["Stats"])
def get_stats(request):
    """Get overall game statistics (public access)"""
    from django.db.models import Sum, Avg, Max
    
    total_players = Player.objects.count()
    total_sessions = GameSession.objects.count()
    total_score = Player.objects.aggregate(Sum("total_score"))["total_score__sum"] or 0
    avg_score = GameSession.objects.aggregate(Avg("score"))["score__avg"] or 0
    highest_score = GameSession.objects.aggregate(Max("score"))["score__max"] or 0
    
    return {
        "total_players": total_players,
        "total_sessions": total_sessions,
        "total_score": total_score,
        "average_score": round(avg_score, 2),
        "highest_score": highest_score,
    }


# World endpoints (public - viewing available game worlds)
@router.get("/worlds", response=List[WorldSchema], tags=["Worlds"])
def list_worlds(request):
    """Get all available game worlds/themes (public access)"""
    from .models import World
    from .schemas import WorldSchema
    return World.objects.all()


@router.get("/worlds/{world_id}", response=WorldSchema, tags=["Worlds"])
def get_world(request, world_id: int):
    """Get a specific world by ID (public access)"""
    from .models import World
    return get_object_or_404(World, id=world_id)


# Achievement endpoints (public viewing, protected for player achievements)
@router.get("/achievements", response=List[AchievementSchema], tags=["Achievements"])
def list_achievements(request):
    """Get all available achievements (public access)"""
    from .models import Achievement
    from .schemas import AchievementSchema
    return Achievement.objects.all()


@router.get("/achievements/{achievement_id}", response=AchievementSchema, tags=["Achievements"])
def get_achievement(request, achievement_id: int):
    """Get a specific achievement by ID (public access)"""
    from .models import Achievement
    return get_object_or_404(Achievement, id=achievement_id)


@router.get("/players/{player_id}/achievements", response=List[PlayerAchievementSchema], tags=["Achievements"], auth=jwt_auth)
def get_player_achievements(request, player_id: int):
    """Get all achievements for a specific player (requires authentication)"""
    from .models import PlayerAchievement
    from .schemas import PlayerAchievementSchema
    player = get_object_or_404(Player, id=player_id)
    achievements = PlayerAchievement.objects.filter(player=player).select_related('achievement')
    
    # Convert to schema format
    result = []
    for pa in achievements:
        result.append({
            "id": pa.id,
            "achievement": {
                "id": pa.achievement.id,
                "name": pa.achievement.name,
                "description": pa.achievement.description,
                "icon": pa.achievement.icon,
                "points": pa.achievement.points,
                "rarity": pa.achievement.rarity,
                "requirement_type": pa.achievement.requirement_type,
                "requirement_value": pa.achievement.requirement_value,
            },
            "earned_at": pa.earned_at,
            "unlocked_at": pa.unlocked_at,
        })
    return result


# Enhanced Profile endpoints
@router.get("/profile/me", response=EnhancedProfileSchema, tags=["Profile"], auth=jwt_auth)
def get_my_profile(request):
    """Get enhanced profile for current authenticated user"""
    from .models import Player, PlayerAchievement
    from .schemas import EnhancedProfileSchema
    
    user = request.auth
    player = get_object_or_404(Player, user=user)
    
    # Get recent achievements (last 5)
    recent_achievements = PlayerAchievement.objects.filter(
        player=player
    ).select_related('achievement').order_by('-unlocked_at')[:5]
    
    recent_list = [
        {
            "id": pa.achievement.id,
            "name": pa.achievement.name,
            "icon": pa.achievement.icon,
            "points": pa.achievement.points,
            "rarity": pa.achievement.rarity,
            "unlocked_at": pa.unlocked_at.isoformat() if pa.unlocked_at else None,
        }
        for pa in recent_achievements
    ]
    
    # Build avatar URL
    avatar_url = None
    if player.avatar:
        avatar_url = request.build_absolute_uri(player.avatar.url)
    
    return {
        "id": player.id,
        "username": player.username,
        "email": player.email or "",
        "total_score": player.total_score,
        "games_played": player.games_played,
        "highest_level": player.highest_level,
        "avatar_url": avatar_url,
        "bio": player.bio or "",
        "bg_color": player.bg_color or "#000000",
        "show_scores": player.show_scores,
        "created_at": player.created_at,
        "updated_at": player.updated_at,
        "achievements_count": PlayerAchievement.objects.filter(player=player).count(),
        "recent_achievements": recent_list,
    }


@router.patch("/profile/me", response=EnhancedProfileSchema, tags=["Profile"], auth=jwt_auth)
def update_my_profile(request, payload: ProfileUpdateSchema):
    """Update current user's profile (requires authentication)"""
    from .models import Player, PlayerAchievement
    
    user = request.auth
    player = get_object_or_404(Player, user=user)
    
    # Update only provided fields
    if payload.username is not None:
        player.username = payload.username
        user.username = payload.username
        user.save()
    
    if payload.email is not None:
        player.email = payload.email
        user.email = payload.email
        user.save()
    
    if payload.bio is not None:
        import re
        # Strip HTML tags to prevent XSS
        player.bio = re.sub(r'<[^>]+>', '', payload.bio)
    
    if payload.bg_color is not None:
        player.bg_color = payload.bg_color
    
    if payload.show_scores is not None:
        player.show_scores = payload.show_scores
    
    player.save()
    
    # Return full profile (same as GET /profile/me)
    avatar_url = None
    if player.avatar:
        avatar_url = request.build_absolute_uri(player.avatar.url)
    
    recent_achievements = PlayerAchievement.objects.filter(
        player=player
    ).select_related('achievement').order_by('-unlocked_at')[:5]
    
    recent_list = [
        {
            "id": pa.achievement.id,
            "name": pa.achievement.name,
            "icon": pa.achievement.icon,
            "points": pa.achievement.points,
            "rarity": pa.achievement.rarity,
            "unlocked_at": pa.unlocked_at.isoformat() if pa.unlocked_at else None,
        }
        for pa in recent_achievements
    ]
    
    return {
        "id": player.id,
        "username": player.username,
        "email": player.email or "",
        "total_score": player.total_score,
        "games_played": player.games_played,
        "highest_level": player.highest_level,
        "avatar_url": avatar_url,
        "bio": player.bio or "",
        "bg_color": player.bg_color or "#000000",
        "show_scores": player.show_scores,
        "created_at": player.created_at,
        "updated_at": player.updated_at,
        "achievements_count": PlayerAchievement.objects.filter(player=player).count(),
        "recent_achievements": recent_list,
    }


@router.post("/profile/me/avatar", tags=["Profile"], auth=jwt_auth)
def upload_avatar(request):
    """Upload avatar image for current user (max 5MB, PNG/JPG/GIF)"""
    from django.core.files.uploadhandler import MemoryFileUploadHandler
    
    user = request.auth
    player = get_object_or_404(Player, user=user)
    
    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        from ninja.responses import Response
        return Response({"error": "No avatar file provided"}, status=400)
    
    # Validate file size (5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        from ninja.responses import Response
        return Response({"error": "File too large. Maximum 5MB."}, status=400)
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        from ninja.responses import Response
        return Response({"error": "Invalid file type. Use PNG, JPG, GIF or WebP."}, status=400)
    
    # Delete old avatar if exists
    if player.avatar:
        player.avatar.delete(save=False)
    
    # Save new avatar
    player.avatar = avatar_file
    player.save()
    
    avatar_url = request.build_absolute_uri(player.avatar.url)
    return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}
