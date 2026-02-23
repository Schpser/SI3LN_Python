from ninja import Schema
from datetime import datetime
from typing import Optional


class PlayerSchema(Schema):
    id: int
    username: str
    email: Optional[str] = ""
    total_score: int
    games_played: int
    highest_level: int
    created_at: datetime


class PlayerCreateSchema(Schema):
    username: str
    email: str


class GameSessionSchema(Schema):
    id: int
    player_id: int
    world_id: Optional[int] = None
    score: int
    level_reached: int
    enemies_killed: int
    duration_seconds: int
    completed: bool
    started_at: datetime
    ended_at: Optional[datetime] = None


class GameSessionCreateSchema(Schema):
    player_id: int
    world_id: Optional[int] = None


class GameSessionUpdateSchema(Schema):
    score: Optional[int] = None
    level_reached: Optional[int] = None
    enemies_killed: Optional[int] = None
    duration_seconds: Optional[int] = None
    completed: Optional[bool] = None
    ended_at: Optional[datetime] = None


class LeaderboardEntrySchema(Schema):
    rank: int
    player_id: int
    player_username: str
    score: int
    level_reached: int
    world_name: Optional[str] = None
    created_at: datetime


class MessageSchema(Schema):
    message: str


class UserSchema(Schema):
    """
    User schema that explicitly excludes password field
    to prevent accidental password hash exposure in API responses
    """
    id: int
    username: str
    email: Optional[str] = ""
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    is_active: bool
    date_joined: datetime
    
    class Config:
        # Explicitly exclude password and other sensitive fields
        exclude = ['password', 'last_login']


# World Schemas
class WorldSchema(Schema):
    id: int
    name: str
    description: Optional[str] = ""
    background_color: str
    difficulty_multiplier: float


# Achievement Schemas
class AchievementSchema(Schema):
    id: int
    name: str
    description: str
    icon: Optional[str] = ""
    points: int
    rarity: str
    requirement_type: str
    requirement_value: int


class PlayerAchievementSchema(Schema):
    id: int
    achievement: AchievementSchema
    earned_at: datetime
    unlocked_at: datetime


# Enhanced Profile Schemas
class EnhancedProfileSchema(Schema):
    id: int
    username: str
    email: Optional[str] = ""
    total_score: int
    games_played: int
    highest_level: int
    created_at: datetime
    updated_at: datetime
    achievements_count: int
    recent_achievements: list = []


class ProfileUpdateSchema(Schema):
    username: Optional[str] = None
    email: Optional[str] = None


# Password Change Schema
class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str


# Account Update Schema
class AccountUpdateSchema(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
