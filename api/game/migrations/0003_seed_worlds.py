"""
Data migration: seed all 5 World records so world-filter tests have data.
"""
from django.db import migrations


WORLDS = [
    {"name": "CLASSIC",  "description": "The original classic space adventure.", "background_color": "#0a0a2e", "difficulty_multiplier": 1.0},
    {"name": "NEON",     "description": "A high-speed neon city run.",           "background_color": "#0d0d0d", "difficulty_multiplier": 1.3},
    {"name": "FOREST",   "description": "Navigate the mystic forest.",           "background_color": "#0b2e0b", "difficulty_multiplier": 1.1},
    {"name": "OCEAN",    "description": "Dive into the deep ocean.",             "background_color": "#001a33", "difficulty_multiplier": 1.2},
    {"name": "DESERT",   "description": "Survive the Mars desert.",              "background_color": "#2e1a00", "difficulty_multiplier": 1.5},
]


def seed_worlds(apps, schema_editor):
    World = apps.get_model("game", "World")
    for w in WORLDS:
        World.objects.get_or_create(name=w["name"], defaults={
            "description": w["description"],
            "background_color": w["background_color"],
            "difficulty_multiplier": w["difficulty_multiplier"],
        })


def unseed_worlds(apps, schema_editor):
    World = apps.get_model("game", "World")
    World.objects.filter(name__in=[w["name"] for w in WORLDS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0002_player_avatar_bio_bgcolor_showscores"),
    ]

    operations = [
        migrations.RunPython(seed_worlds, reverse_code=unseed_worlds),
    ]
