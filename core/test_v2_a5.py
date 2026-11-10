from datetime import datetime, timedelta, timezone as dt_timezone
from io import StringIO
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson, LiveSession, Module
from users.models import Notification

User = get_user_model()
PASSWORD = 'StrongPassword123!'
MEET = 'https://meet.google.com/abc-defg-hij'


class A5Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.bls = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls', creator=self.admin.creator_profile,
                                         status='published', live_meet_url=MEET)
        self.acls = Course.objects.create(title='Suporte Avançado ACLS', short_name='ACLS', slug='acls', creator=self.admin.creator_profile,
                                          status='published')
        self.enroll = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Enrollment.objects.create(student=self.jane.student_profile, course=self.acls)
        Enrollment.objects.create(student=self.ana.student_profile, course=self.bls)
        self.now = timezone.now()
        self.client.force_login(self.jane)

    def session(self, course=None, start=timedelta(days=2), length=timedelta(hours=1, minutes=30), **extra):
        starts = self.now + start
        return LiveSession.objects.create(course=course or self.bls, title=extra.pop('title', 'Encontro'), starts_at=starts,
                                          ends_at=starts + length, **extra)

    def page(self, **params):
        return self.client.get(reverse('live_classes'), params)


class LivePageTests(A5Base):
    def test_empty_state_without_any_session(self):
        response = self.page()
        self.assertContains(response, 'Nenhum dos seus cursos tem aulas ao vivo no momento.')
        self.assertNotContains(response, 'Próximo encontro')

    def test_staff_goes_to_painel(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.page(), reverse('painel:dashboard'), fetch_redirect_response=False)

    def test_no_google_calendar_embed_any_more(self):
        self.session()
        self.assertNotContains(self.page(), 'calendar/embed')
        self.assertNotContains(self.page(), '<iframe')

    def test_scheduled_session_locks_the_meet_button(self):
        session = self.session(start=timedelta(days=2), host_name='Dr. Rafael Souza')
        html = self.page().content.decode()
        self.assertIn('Próximo encontro', html)
        self.assertIn('Em 2 dias', html)
        self.assertIn('aria-disabled="true"', html)
        self.assertIn('data-enable-at="' + (session.starts_at - timedelta(minutes=15)).astimezone(dt_timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + '"', html)
        self.assertIn(f'data-enabled-href="{MEET}"', html)
        self.assertIn('<span data-lock-icon>', html)
        self.assertIn('O botão de entrar libera 15 minutos antes do início. Você recebe um lembrete por e-mail 1 hora antes.', html)
        self.assertIn('data-enabled-hint="A sala já está aberta. O link abre o Google Meet em uma nova aba."', html)
        self.assertIn('Dr. Rafael Souza', html)
        self.assertIn('(horário de Brasília)', html)
        self.assertNotIn(f'href="{MEET}" target="_blank"', html)

    def test_soon_session_opens_the_button(self):
        self.session(start=timedelta(minutes=10, seconds=30))
        html = self.page().content.decode()
        self.assertIn('Começa em 11 min', html)
        self.assertIn('is-soon', html)
        self.assertIn(f'href="{MEET}" target="_blank" rel="noopener"', html)
        self.assertIn('A sala já está aberta. O link abre o Google Meet em uma nova aba.', html)
        self.assertNotIn('data-enable-at', html)
        self.assertNotIn('data-lock-icon', html)

    def test_live_session_state(self):
        self.session(start=-timedelta(minutes=12))
        html = self.page().content.decode()
        self.assertIn('● Ao vivo agora', html)
        self.assertIn('badge--live', html)
        self.assertIn('is-live', html)
        self.assertIn('Começou há 12 minutos. Ainda dá tempo de entrar.', html)

    def test_singular_minute(self):
        self.session(start=-timedelta(minutes=1, seconds=10))
        self.assertContains(self.page(), 'Começou há 1 minuto. Ainda dá tempo de entrar.')

    def test_badge_for_tomorrow_and_today(self):
        tomorrow = self.session(start=timedelta(days=1))
        self.assertContains(self.page(), '>Amanhã<')
        tomorrow.delete()
        today_start = max(timedelta(minutes=30), timedelta(hours=1))
        session = self.session(start=today_start)
        local_now = timezone.localtime(self.now, ZoneInfo('America/Sao_Paulo'))
        local_start = timezone.localtime(session.starts_at, ZoneInfo('America/Sao_Paulo'))
        label = 'Hoje às ' if local_start.date() == local_now.date() else 'Amanhã'
        self.assertContains(self.page(), label)

    def test_time_is_shown_in_brasilia(self):
        starts = datetime(2099, 11, 12, 23, 0, tzinfo=dt_timezone.utc)
        LiveSession.objects.create(course=self.bls, title='Encontro 3', starts_at=starts, ends_at=starts + timedelta(hours=1, minutes=30))
        html = self.page().content.decode()
        self.assertIn('20h00 às 21h30 (horário de Brasília)', html)
        self.assertIn('date-tile__wd">Qui<', html)
        self.assertIn('date-tile__day">12<', html)
        self.assertIn('date-tile__mon">nov<', html)

    def test_only_own_active_courses_are_listed(self):
        other = Course.objects.create(title='Outro', slug='outro', creator=self.admin.creator_profile, status='published')
        self.session(course=other, title='Invisível')
        self.session(title='Visível')
        html = self.page().content.decode()
        self.assertIn('Visível', html)
        self.assertNotIn('Invisível', html)
        self.enroll.is_active = False
        self.enroll.save()
        self.assertNotContains(self.page(), 'Visível')

    def test_agenda_marks_first_as_next_and_limits_to_ten(self):
        for index in range(12):
            self.session(start=timedelta(days=index + 1), title=f'Encontro {index + 1}')
        response = self.page()
        self.assertEqual(len(response.context['upcoming']), 10)
        html = response.content.decode()
        self.assertEqual(html.count('>Próximo<'), 1)
        self.assertEqual(html.count('>Agendado<'), 9)
        self.assertIn('Adicionar ao Google Agenda', html)

    def test_chips_filter_by_course_and_show_empty_state(self):
        self.session(title='Só do BLS')
        html = self.page().content.decode()
        for chip in ('Todos os cursos', '>BLS<', '>ACLS<'):
            self.assertIn(chip, html)
        filtered = self.page(curso='acls')
        self.assertContains(filtered, 'O ACLS não tem encontros ao vivo marcados')
        self.assertContains(filtered, 'Quando a equipe marcar, você recebe um e-mail com data e link, e o encontro aparece aqui.')
        self.assertContains(self.page(curso='bls'), 'Só do BLS')
        self.assertEqual(self.page(curso='nao-existe').context['selected_course'], None)

    def test_google_calendar_link(self):
        session = self.session(title='Casos de sala vermelha')
        html = self.page().content.decode()
        self.assertIn('https://calendar.google.com/calendar/render?action=TEMPLATE', html)
        self.assertIn('dates=' + session.starts_at.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ'), html)
        self.assertIn('location=Google+Meet', html)
        self.assertIn('Casos+de+sala+vermelha', html)

    def test_session_without_link_has_no_meet_button(self):
        self.bls.live_meet_url = ''
        self.bls.save()
        self.session()
        html = self.page().content.decode()
        self.assertNotIn('Entrar no Google Meet', html)
        self.assertIn('Baixar convite (.ics)', html)

    def test_session_link_overrides_course_link(self):
        self.session(meet_url='https://meet.google.com/zzz-zzzz-zzz', start=timedelta(minutes=5))
        self.assertContains(self.page(), 'https://meet.google.com/zzz-zzzz-zzz')

    def test_ended_sessions_leave_the_agenda(self):
        self.session(start=-timedelta(days=3), title='Encontro antigo')
        self.assertNotContains(self.page(), 'Encontro antigo</span>')
        self.assertEqual(self.page().context['next_session'], None)


class RecordingsTests(A5Base):
    def test_recordings_available_for_thirty_days_by_default(self):
        self.session(start=-timedelta(days=5), title='Encontro 2', recording_url='https://vimeo.com/76979871')
        response = self.page()
        html = response.content.decode()
        self.assertIn('Gravações', html)
        self.assertIn('Perdeu um encontro? A gravação fica disponível por 30 dias.', html)
        self.assertIn('https://vimeo.com/76979871', html)
        self.assertIn('1h30', html)
        self.assertRegex(html, r'Gravado em \d\d/\d\d · disponível até \d\d/\d\d')
        self.assertEqual(len(response.context['recordings']), 1)

    def test_expired_missing_and_future_recordings_are_hidden(self):
        self.session(start=-timedelta(days=40), title='Expirada', recording_url='https://vimeo.com/1')
        self.session(start=-timedelta(days=2), title='Sem gravação')
        self.session(start=-timedelta(days=3), title='Até ontem', recording_url='https://vimeo.com/2',
                     recording_until=timezone.localdate() - timedelta(days=1))
        self.session(start=timedelta(days=3), title='Futura', recording_url='https://vimeo.com/3')
        self.assertEqual(self.page().context['recordings'], [])
        self.assertNotContains(self.page(), 'Gravações')

    def test_explicit_until_date_extends_availability(self):
        self.session(start=-timedelta(days=40), title='Estendida', recording_url='https://vimeo.com/9',
                     recording_until=timezone.localdate() + timedelta(days=2))
        self.assertEqual(len(self.page().context['recordings']), 1)

    def test_recordings_ignore_course_filter_and_other_courses(self):
        other = Course.objects.create(title='Outro', slug='outro', creator=self.admin.creator_profile, status='published')
        self.session(course=other, start=-timedelta(days=2), recording_url='https://vimeo.com/5', title='De outro curso')
        self.session(start=-timedelta(days=2), recording_url='https://vimeo.com/6', title='Do BLS')
        response = self.page(curso='acls')
        self.assertEqual([r.title for r in response.context['recordings']], ['Do BLS'])


class IcsTests(A5Base):
    def get(self, session):
        return self.client.get(reverse('live_session_ics', args=[session.id]))

    def test_content_and_headers(self):
        session = self.session(title='Casos de sala vermelha')
        response = self.get(session)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/calendar'))
        self.assertIn('attachment', response['Content-Disposition'])
        text = response.content.decode()
        self.assertTrue(text.startswith('BEGIN:VCALENDAR\r\n'))
        self.assertTrue(text.endswith('END:VCALENDAR\r\n'))
        self.assertIn('DTSTART:' + session.starts_at.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ'), text)
        self.assertIn('DTEND:' + session.ends_at.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ'), text)
        self.assertIn('SUMMARY:Suporte Básico de Vida · Casos de sala vermelha', text)
        self.assertIn('LOCATION:' + MEET, text)
        self.assertIn('DESCRIPTION:Link do Google Meet: ' + MEET, text)
        self.assertIn(f'UID:live-{session.id}@testserver', text)

    def test_line_endings_and_folding(self):
        session = self.session(title='T' * 200)
        text = self.get(session).content.decode()
        self.assertNotIn('\n', text.replace('\r\n', ''))
        for line in text.split('\r\n'):
            self.assertLessEqual(len(line.encode('utf-8')), 75, line)
        unfolded = text.replace('\r\n ', '')
        self.assertIn('T' * 200, unfolded)

    def test_special_characters_are_escaped(self):
        session = self.session(title='Casos; vias aéreas, difíceis')
        unfolded = self.get(session).content.decode().replace('\r\n ', '')
        self.assertIn('Casos\\; vias aéreas\\, difíceis', unfolded)

    def test_no_location_without_link(self):
        self.bls.live_meet_url = ''
        self.bls.save()
        text = self.get(self.session()).content.decode()
        self.assertNotIn('LOCATION', text)
        self.assertNotIn('DESCRIPTION', text)

    def test_access_rules(self):
        session = self.session()
        self.assertEqual(self.client.get(reverse('live_session_ics', args=[999999])).status_code, 404)
        self.client.force_login(User.objects.create_user(username='x', email='x@example.com', password=PASSWORD))
        self.assertEqual(self.get(session).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.get(session).status_code, 404)
        self.client.logout()
        self.assertEqual(self.get(session).status_code, 302)

    def test_inactive_enrollment_cannot_download(self):
        session = self.session()
        self.enroll.is_active = False
        self.enroll.save()
        self.assertEqual(self.get(session).status_code, 404)


class LiveRemindersTests(A5Base):
    def run_command(self):
        out = StringIO()
        call_command('live_reminders', stdout=out)
        return out.getvalue()

    def test_notifies_enrolled_students_in_the_window_once(self):
        session = self.session(start=timedelta(minutes=65), title='Encontro 3')
        self.assertEqual(self.run_command().strip(), '2 aviso(s) enviado(s).')
        self.assertEqual(Notification.objects.filter(kind='live').count(), 2)
        notification = Notification.objects.get(user=self.jane, kind='live')
        clock = timezone.localtime(session.starts_at, ZoneInfo('America/Sao_Paulo')).strftime('%H:%M')
        self.assertEqual(notification.title, f'Aula ao vivo hoje às {clock}')
        self.assertEqual(notification.meta, 'BLS · Encontro 3')
        self.assertEqual(notification.url, '/ao-vivo/')
        self.assertEqual(len(mail.outbox), 2)
        session.refresh_from_db()
        self.assertIsNotNone(session.reminder_sent_at)
        self.assertEqual(self.run_command().strip(), '0 aviso(s) enviado(s).')
        self.assertEqual(Notification.objects.filter(kind='live').count(), 2)

    def test_window_edges(self):
        self.session(start=timedelta(minutes=59), title='Cedo demais?')
        self.session(start=timedelta(minutes=76), title='Longe')
        self.session(start=-timedelta(minutes=5), title='Já começou')
        self.assertEqual(self.run_command().strip(), '0 aviso(s) enviado(s).')
        self.assertEqual(Notification.objects.count(), 0)
        inside = self.session(start=timedelta(minutes=74), title='Dentro')
        self.assertEqual(self.run_command().strip(), '2 aviso(s) enviado(s).')
        self.assertTrue(LiveSession.objects.get(pk=inside.pk).reminder_sent_at)

    def test_respects_email_preference_and_enrollment_state(self):
        profile = self.jane.student_profile
        profile.notify_live = False
        profile.save()
        self.enroll_other = Enrollment.objects.filter(student=self.ana.student_profile, course=self.bls).update(is_active=False)
        self.session(start=timedelta(minutes=65))
        self.run_command()
        self.assertEqual(Notification.objects.filter(kind='live').count(), 1)
        self.assertEqual(Notification.objects.get(kind='live').user, self.jane)
        self.assertEqual(len(mail.outbox), 0)

    def test_expired_access_is_skipped(self):
        self.enroll.expires_at = timezone.now() - timedelta(days=1)
        self.enroll.save()
        self.session(start=timedelta(minutes=65))
        self.run_command()
        self.assertEqual(list(Notification.objects.values_list('user_id', flat=True)), [self.ana.id])

    @override_settings(SITE_URL='https://escola.example.com')
    def test_email_link_uses_site_url_outside_requests(self):
        self.session(start=timedelta(minutes=65))
        self.run_command()
        self.assertIn('https://escola.example.com/ao-vivo/', mail.outbox[0].body)

    def test_other_courses_students_are_not_notified(self):
        self.session(course=self.acls, start=timedelta(minutes=65))
        self.run_command()
        self.assertEqual(list(Notification.objects.values_list('user_id', flat=True)), [self.jane.id])


class ReleaseModulesTests(A5Base):
    def setUp(self):
        super().setUp()
        self.bls.release_mode = 'scheduled'
        self.bls.save()
        self.module = Module.objects.create(course=self.bls, title='Prática', order=2)
        Lesson.objects.create(module=self.module, title='Aula', order=1)

    def run_command(self):
        out = StringIO()
        call_command('release_modules', stdout=out)
        return out.getvalue().strip()

    def test_days_after_enrollment_release_notifies_once(self):
        self.module.release_after_days = 7
        self.module.save()
        Enrollment.objects.filter(pk=self.enroll.pk).update(enrolled_at=timezone.now() - timedelta(days=7, hours=2))
        Enrollment.objects.filter(student=self.ana.student_profile).update(enrolled_at=timezone.now() - timedelta(days=2))
        self.assertEqual(self.run_command(), '1 aviso(s) enviado(s).')
        notification = Notification.objects.get(kind='module')
        self.assertEqual((notification.user, notification.title, notification.meta, notification.url),
                         (self.jane, 'Novo módulo liberado', 'BLS · Prática', '/meus-cursos/bls/'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.run_command(), '0 aviso(s) enviado(s).')
        self.assertEqual(Notification.objects.filter(kind='module').count(), 1)

    def test_fixed_date_release_covers_everyone(self):
        self.module.release_date = timezone.localdate()
        self.module.save()
        self.assertEqual(self.run_command(), '2 aviso(s) enviado(s).')

    def test_release_older_than_a_day_or_in_the_future_is_ignored(self):
        self.module.release_date = timezone.localdate() - timedelta(days=2)
        self.module.save()
        self.assertEqual(self.run_command(), '0 aviso(s) enviado(s).')
        self.module.release_date = timezone.localdate() + timedelta(days=2)
        self.module.save()
        self.assertEqual(self.run_command(), '0 aviso(s) enviado(s).')

    def test_course_with_everything_released_at_enrollment_is_ignored(self):
        self.bls.release_mode = 'all'
        self.bls.save()
        self.module.release_date = timezone.localdate()
        self.module.save()
        self.assertEqual(self.run_command(), '0 aviso(s) enviado(s).')

    def test_email_follows_course_flag_but_bell_notification_stays(self):
        self.bls.notify_module_release = False
        self.bls.save()
        self.module.release_date = timezone.localdate()
        self.module.save()
        self.run_command()
        self.assertEqual(Notification.objects.filter(kind='module').count(), 2)
        self.assertEqual(len(mail.outbox), 0)

    def test_inactive_and_archived_are_skipped(self):
        self.module.release_date = timezone.localdate()
        self.module.save()
        Enrollment.objects.filter(pk=self.enroll.pk).update(is_active=False)
        self.assertEqual(self.run_command(), '1 aviso(s) enviado(s).')
        self.bls.status = 'archived'
        self.bls.save()
        Notification.objects.all().delete()
        self.assertEqual(self.run_command(), '0 aviso(s) enviado(s).')
