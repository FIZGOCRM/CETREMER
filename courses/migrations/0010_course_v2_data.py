import re

from django.db import migrations


def forwards(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Module = apps.get_model('courses', 'Module')
    Course.objects.filter(is_published=True).update(status='published')
    Course.objects.filter(is_published=False).update(status='draft')
    # HANDOFF-v2 seção 10, item 2: título do módulo sem o prefixo "Módulo N:".
    for module in Module.objects.all():
        title = re.sub(r'^Módulo \d+:\s*', '', module.title)
        if title != module.title and title:
            module.title = title
            module.save(update_fields=['title'])


def backwards(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Course.objects.filter(status='published').update(is_published=True)
    Course.objects.exclude(status='published').update(is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_course_v2_schema'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
