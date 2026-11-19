from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image

from courses.models import Course, HomeFeature, Lesson, Module, Progress, WeeklySelectionItem
from users.models import User


class LessonAnalyticsTests(TestCase):
    def cover_upload(self):
        stream = BytesIO()
        Image.new('RGB', (20, 30)).save(stream, format='PNG')
        return SimpleUploadedFile('poster.png', stream.getvalue(), content_type='image/png')

    def setUp(self):
        self.owner = User.objects.create_user(username='mentor', role='CREATOR')
        self.course = Course.objects.create(title='Mentoria', slug='mentoria', creator=self.owner.creator_profile)
        module = Module.objects.create(course=self.course, title='Respiração')
        self.lesson = Lesson.objects.create(module=module, title='Aula com vídeo', duration_seconds=100)
        self.unknown = Lesson.objects.create(module=module, title='Aula sem duração')
        self.client.force_login(self.owner)
        self.url = '/painel/relatorios/aulas/'
        self.now = timezone.now()

    def progress(self, name, lesson=None, age=0, **kwargs):
        user = User.objects.create_user(username=name)
        return Progress.objects.create(lesson=lesson or self.lesson, student=user.student_profile,
                                       started_at=self.now - timedelta(days=age), **kwargs)

    def test_report_reachable_only_by_producer(self):
        self.assertContains(self.client.get('/painel/relatorios/'), self.url)
        self.assertContains(self.client.get(self.url), 'Sem duração')
        student = User.objects.create_user(username='aluno')
        self.client.force_login(student)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        weekly = f'/painel/cursos/{self.course.pk}/top-10/'
        self.assertEqual(self.client.get(weekly).status_code, 403)
        self.assertEqual(self.client.post(weekly, {}).status_code, 403)

    def test_percentages_and_histogram_use_starters_and_highest_position(self):
        self.progress('credit-only', watched_seconds=5)
        self.progress('quarter', last_position_seconds=25, manual_completed_at=self.now)
        self.progress('half', max_position_seconds=50, auto_completed_at=self.now)
        self.progress('three-quarters', max_position_seconds=75)
        self.progress('threshold', max_position_seconds=90, last_position_seconds=2)
        self.progress('beyond', max_position_seconds=111)
        self.progress('never-started', is_completed=True, manual_completed_at=self.now)
        self.progress('unknown', self.unknown, watched_seconds=10)
        response = self.client.get(self.url, {'curso': self.course.pk, 'dias': 'tudo', 'ordem': '-started'})
        row, unknown = response.context['rows']
        self.assertEqual(row['lesson'], self.lesson)
        self.assertEqual((row['started'], row['finished'], row['manual']), (6, 3, 2))
        self.assertEqual(row['finish_pct'], 50)
        self.assertAlmostEqual(row['avg_pct'], 340 / 6)
        self.assertEqual(row['bands'], [1, 1, 1, 3])
        self.assertIsNone(unknown['avg_pct'])
        self.assertContains(response, 'Sem duração')
        ascending = self.client.get(self.url, {'ordem': 'started'})
        self.assertEqual(ascending.context['rows'][0]['lesson'], self.unknown)

    def test_filter_uses_first_start_and_preserves_unknown_legacy_date_only_in_all(self):
        self.progress('recent', watched_seconds=4)
        self.progress('old', age=12, last_position_seconds=2, last_heartbeat_at=self.now)
        record = self.progress('undated', watched_seconds=10)
        Progress.objects.filter(pk=record.pk).update(started_at=None)
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        Lesson.objects.create(module=Module.objects.create(course=other, title='Outro'), title='Fora do curso')
        for days, expected in [('7', 1), ('30', 2), ('tudo', 3)]:
            with self.subTest(days=days):
                response = self.client.get(self.url, {'curso': self.course.pk, 'dias': days, 'ordem': '-started'})
                self.assertNotContains(response, 'Fora do curso')
                self.assertEqual(response.context['rows'][0]['started'], expected)

    def test_top_ten_editor_validates_positions_and_course_and_preserves_previous_weeks(self):
        from courses.models import WeeklySelection
        url = f'/painel/cursos/{self.course.pk}/top-10/'
        week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        outsider = Lesson.objects.create(module=Module.objects.create(course=other, title='Outro'), title='Outra')
        fields = {'lesson_2': self.lesson.pk, 'lesson_1': self.unknown.pk}
        data = {'semana': week.isoformat(), **fields}
        self.assertRedirects(self.client.post(url, data), f'{url}?semana={week}')
        selection = WeeklySelection.objects.get(course=self.course, week_start=week)
        self.assertEqual(selection.created_by, self.owner)
        expected = [(self.unknown.pk, 1), (self.lesson.pk, 2)]
        for change in [{'lesson_2': self.unknown.pk}, {'lesson_3': outsider.pk},
                       {'lesson_11': self.lesson.pk}, {'semana': week + timedelta(days=1)}]:
            with self.subTest(change=change):
                response = self.client.post(url, {**data, **change})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertEqual(list(selection.items.order_by('position').values_list('lesson_id', 'position')), expected)
        next_week = week + timedelta(days=7)
        self.client.post(url, {'semana': next_week, 'lesson_1': self.lesson.pk})
        response = self.client.get(url, {'semana': next_week})
        self.assertContains(response, f'?semana={week}')
        self.assertContains(response, 'Chegaram ao final')
        self.assertEqual(WeeklySelection.objects.filter(course=self.course).count(), 2)
        self.client.post(url, {'semana': week, 'lesson_1': self.lesson.pk})
        self.assertEqual(list(selection.items.values_list('lesson_id', 'position')), [(self.lesson.pk, 1)])

    def test_selection_service_enforces_permissions_and_rules_before_replacing_items(self):
        from courses.engagement_services import save_weekly_selection
        from courses.models import WeeklySelection

        week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        def save(positions, monday=week, actor=self.owner):
            return save_weekly_selection(self.course, monday, positions, actor=actor)

        selection = save({1: self.lesson.pk})
        outsiders = Module.objects.create(course=Course.objects.create(
            title='Externo', slug='externo', creator=self.owner.creator_profile), title='Outro')
        foreign = Lesson.objects.create(module=outsiders, title='Externa')
        for invalid in [{0: self.unknown.pk}, {11: self.lesson.pk}, {1: foreign.pk},
                        {1: self.unknown.pk, 2: self.unknown.pk}]:
            with self.subTest(positions=invalid), self.assertRaises(ValidationError):
                save(invalid)
        with self.assertRaises(ValidationError):
            save({}, monday=week + timedelta(days=1))
        with self.assertRaises(PermissionDenied):
            save({}, actor=User.objects.create_user(username='aluno'))
        self.assertEqual(list(selection.items.values_list('position', 'lesson_id')), [(1, self.lesson.pk)])
        self.assertEqual(WeeklySelection.objects.count(), 1)

    def test_weekly_poster_follows_lesson_on_reorder_and_can_be_cleared(self):
        url = f'/painel/cursos/{self.course.pk}/top-10/'
        week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            response = self.client.post(url, {'semana': week, 'lesson_1': self.lesson.pk, 'art_1': self.cover_upload()})
            self.assertEqual(response.status_code, 302)
            art = WeeklySelectionItem.objects.get().artwork
            self.assertTrue(art.storage.exists(art.name))
            data = {'semana': week, 'lesson_2': self.lesson.pk}
            self.assertEqual(self.client.post(url, data).status_code, 302)
            self.assertEqual(WeeklySelectionItem.objects.get().artwork.name, art.name)
            self.assertEqual(self.client.post(url, {**data, 'art_2-clear': 'on'}).status_code, 302)
            self.assertFalse(WeeklySelectionItem.objects.get().artwork)

    def test_producer_manages_home_cards_and_cannot_select_another_courses_lesson(self):
        url = f'/painel/cursos/{self.course.pk}/inicio/'
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile, is_published=True)
        foreign = Lesson.objects.create(module=Module.objects.create(course=other, title='Módulo'), title='De fora')
        self.assertContains(self.client.get(url), 'Adicionar card')
        self.assertEqual(self.client.post(url, {'target': f'lesson:{foreign.pk}', 'position': 1}).status_code, 200)
        self.assertFalse(HomeFeature.objects.exists())
        data = {'target': f'lesson:{self.lesson.pk}', 'position': 1}
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            self.assertRedirects(self.client.post(url, {**data, 'artwork': self.cover_upload()}), url)
            entry = HomeFeature.objects.get()
            self.assertTrue(entry.artwork.storage.exists(entry.artwork.name))
            self.assertContains(self.client.post(url, data), 'já está na seção')
            self.assertRedirects(self.client.post(url, {'item': entry.pk, 'target': f'offer:{other.pk}', 'position': 4}), url)
            entry.refresh_from_db()
            self.assertEqual((entry.target, entry.position, entry.lesson_id), (other, 4, None))
            self.assertTrue(entry.artwork)
            self.assertEqual(self.client.get(f'/painel/cursos/{other.pk}/inicio/?item={entry.pk}').status_code, 404)
            self.assertRedirects(self.client.post(url, {'item': entry.pk, 'action': 'remove'}), url)
            self.assertFalse(HomeFeature.objects.exists())
        self.client.force_login(User.objects.create_user(username='aluna'))
        self.assertEqual(self.client.post(url, data).status_code, 403)
