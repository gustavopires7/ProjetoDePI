# Generated by Django 5.1.4 on 2024-12-11 00:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profissional',
            old_name='descricao_servicos',
            new_name='biografia',
        ),
        migrations.RemoveField(
            model_name='profissional',
            name='registro_profissional',
        ),
        migrations.AddField(
            model_name='profissional',
            name='CRM',
            field=models.IntegerField(default=None, unique=True),
        ),
    ]
