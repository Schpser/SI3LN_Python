# Generated manually — adds avatar, bio, bg_color, show_scores to Player

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
        migrations.AddField(
            model_name='player',
            name='bio',
            field=models.TextField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='player',
            name='bg_color',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='player',
            name='show_scores',
            field=models.BooleanField(default=True),
        ),
    ]
