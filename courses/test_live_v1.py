from datetime import timedelta
from django.core.exceptions import PermissionDenied,ValidationError
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from courses.models import Course,Enrollment
from users.models import User

class LiveEventTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='live-admin',role='CREATOR')
        self.user=User.objects.create_user(username='live-member')
        self.other=User.objects.create_user(username='live-other')
        self.course=Course.objects.create(title='Saúde ao vivo',slug='live-course',creator=self.admin.creator_profile)
        Enrollment.objects.create(student=self.user.student_profile,course=self.course)
        self.client.force_login(self.user)

    def event(self,**kwargs):
        from courses.models import LiveEvent
        data=dict(course=self.course,title='Encontro de demonstração',starts_at=timezone.now()+timedelta(hours=1),duration_minutes=60,room_url='https://example.org/sala-reservada',recording_url='https://example.org/gravacao-reservada')
        data.update(kwargs);return LiveEvent.objects.create(**data)

    def test_course_event_is_invisible_to_outsider(self):
        event=self.event();self.client.force_login(self.other)
        self.assertNotContains(self.client.get('/ao-vivo/'),event.title)
        self.assertEqual(self.client.get(f'/ao-vivo/{event.pk}/sala/').status_code,403)

    def test_room_url_not_exposed_before_ten_minutes_and_opens_at_boundary(self):
        event=self.event();now=event.starts_at-timedelta(minutes=10)
        self.assertNotContains(self.client.get('/ao-vivo/'),'sala-reservada')
        self.assertEqual(self.client.get(f'/ao-vivo/{event.pk}/sala/').status_code,403)
        with patch('courses.live_services.timezone.now',return_value=now):
            response=self.client.get(f'/ao-vivo/{event.pk}/sala/')
        self.assertEqual(response.status_code,302);self.assertEqual(response.url,event.room_url)

    def test_general_event_requires_any_active_course(self):
        from courses.live_services import require_event_access
        event=self.event(course=None)
        require_event_access(self.user,event)
        with self.assertRaises(PermissionDenied):require_event_access(self.other,event)

    def test_reminder_toggle_is_unique(self):
        from courses.live_services import toggle_reminder
        from courses.models import LiveReminder
        event=self.event();toggle_reminder(self.user,event);self.assertEqual(LiveReminder.objects.count(),1)
        toggle_reminder(self.user,event);self.assertEqual(LiveReminder.objects.count(),0)
        with self.assertRaises(PermissionDenied):toggle_reminder(self.other,event)

    def test_past_recording_remains_gated_and_in_agenda(self):
        event=self.event(starts_at=timezone.now()-timedelta(days=1))
        self.assertContains(self.client.get('/ao-vivo/'),'Gravações')
        self.assertEqual(self.client.get(f'/ao-vivo/{event.pk}/gravacao/').status_code,302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/ao-vivo/{event.pk}/gravacao/').status_code,403)

    def test_end_of_plan_revokes_room_and_recording(self):
        from courses.live_services import require_event_access
        enrollment=Enrollment.objects.get();enrollment.access_policy='PERIODS';enrollment.save()
        with self.assertRaises(PermissionDenied):require_event_access(self.user,self.event())

    def test_only_team_can_save_and_remove_preserves_reminders(self):
        from courses.live_services import save_event,remove_event
        from courses.models import LiveReminder
        event=self.event();LiveReminder.objects.create(student=self.user.student_profile,event=event)
        with self.assertRaises(PermissionDenied):save_event(self.user,event)
        remove_event(self.admin,event);event.refresh_from_db();self.assertFalse(event.is_active)
        self.assertEqual(LiveReminder.objects.count(),1)

    def test_next_steps_include_next_event(self):
        from courses.selectors import member_summary
        self.event()
        self.assertTrue(any(step['priority']==7 for step in member_summary(self.user.student_profile)['next_steps']))
