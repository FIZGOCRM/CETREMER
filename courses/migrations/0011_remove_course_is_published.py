from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_course_v2_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='is_published',
        ),
    ]
