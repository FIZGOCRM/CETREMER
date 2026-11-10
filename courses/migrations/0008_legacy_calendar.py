from html.parser import HTMLParser
from urllib.parse import urlparse
from django.db import migrations


class IframeSource(HTMLParser):
    src = ''
    def handle_starttag(self, tag, attrs):
        if tag == 'iframe' and not self.src:
            self.src = dict(attrs).get('src', '')


def forwards(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    for course in Course.objects.exclude(live_schedule_embed__isnull=True).exclude(live_schedule_embed=''):
        if course.live_calendar_url:
            continue
        parser = IframeSource()
        parser.feed(course.live_schedule_embed)
        if urlparse(parser.src).hostname == 'calendar.google.com':
            course.live_calendar_url = parser.src
            course.save(update_fields=['live_calendar_url'])


class Migration(migrations.Migration):
    dependencies = [('courses', '0007_category_remove_lesson_download_name_and_more')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
