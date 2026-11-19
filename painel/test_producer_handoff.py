from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from community.models import CommunityPost
from courses.models import Course, Enrollment, LiveEvent
from users.models import User


class ProducerHandoffTests(TestCase):
    def setUp(self):
        self.producer = User.objects.create_user(username="staff-demo", role="CREATOR")
        self.student = User.objects.create_user(username="learner", email="learner@example.test")
        self.course = Course.objects.create(slug="principal", title="Principal", is_published=True,
                                           creator=self.producer.creator_profile)
        Enrollment.objects.create(student=self.student.student_profile, course=self.course)
        self.client.force_login(self.producer)

    def test_switch_account_keeps_top_ten_destination_and_permissions(self):
        ranking = reverse("painel:weekly_selection", args=[self.course.pk])
        self.client.force_login(self.student)
        response = self.client.get(ranking)
        self.assertContains(response, "Trocar para conta de produtor", status_code=403)
        self.assertEqual(self.client.post(ranking, {}).status_code, 403)
        response = self.client.post(reverse("logout"), {"trocar": "produtor", "next": ranking}, follow=True)
        self.assertTemplateUsed(response, "login_admin.html")
        self.assertEqual(response.context["next"], ranking)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_community_permalink_matches_selected_topic_and_filters(self):
        first = CommunityPost.objects.create(author=self.student, title="Pergunta A", content="Detalhe A")
        second = CommunityPost.objects.create(author=self.student, title="Pergunta B", content="Detalhe B")
        response = self.client.get(reverse("painel:community"), {"status":"new", "topico":second.pk})
        self.assertEqual(response.context["selected"], second)
        self.assertContains(response, first.title)
        self.assertNotContains(response, first.content)

    def test_first_access_code_displayed_once_with_delivery_instructions(self):
        response = self.client.post(reverse("painel:students"), {"action":"generate_first_access",
                                    "student_id":self.student.pk}, follow=True)
        self.assertContains(response, 'id="first-code"')
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertNotContains(self.client.get(response.request["PATH_INFO"], {"aluno":self.student.pk}), 'id="first-code"')

    def test_filtered_live_list_and_preview_course_context(self):
        for name, age in (("Futuro", 3), ("Gravação", -2)):
            LiveEvent.objects.create(title=name, course=self.course, starts_at=timezone.now()+timedelta(days=age))
        response = self.client.get(reverse("painel:live"), {"aba":"passados", "curso":self.course.pk})
        self.assertEqual([event.title for event in response.context["events"]], ["Gravação"])
        another = User.objects.create_user(username="outra")
        path = reverse("painel:preview_choose")
        response = self.client.get(path, {"curso":self.course.pk})
        self.assertNotContains(response, another.username)
        origin = reverse("painel:course_overview", args=[self.course.pk])
        opened = self.client.get(reverse("painel:preview_start", args=[self.student.pk]), {"curso":self.course.pk,"next":origin})
        self.assertRedirects(opened, reverse("course_home", args=[self.course.slug]), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse("painel:preview_end")), origin, fetch_redirect_response=False)

    def test_invalid_plan_returns_to_drawer_with_values_and_explanation(self):
        from courses.services import create_plan

        enrollment = Enrollment.objects.get(course=self.course, student=self.student.student_profile)
        today = timezone.localdate()
        create_plan(enrollment, today, today + timedelta(days=30), actor=self.producer)
        response = self.client.post(reverse("painel:plan_manage", args=[enrollment.pk]), {
            "drawer_mode": "end", "action": "end", "end_date": today.isoformat(),
            "reason_code": "other", "reason_text": "",
        }, follow=True)
        self.assertTemplateUsed(response, "painel/partials/student_drawer.html")
        item = response.context["selected"].enrollment_items[0]
        self.assertEqual(item["retry"]["values"]["reason_code"], "other")
        self.assertTrue(item["retry"]["errors"])
        self.assertFalse(enrollment.access_periods.get().ended_early)

    def test_pending_plan_only_offers_date_correction(self):
        from courses.services import create_plan

        enrollment = Enrollment.objects.get(course=self.course, student=self.student.student_profile)
        start = timezone.localdate() + timedelta(days=12)
        create_plan(enrollment, start, start + timedelta(days=30), actor=self.producer)
        response = self.client.get(reverse("painel:students"), {"aluno": self.student.pk})
        self.assertContains(response, "Corrigir datas")
        self.assertNotContains(response, "Estender acesso")
        self.assertNotContains(response, "Encerrar plano")

    def test_creation_errors_reopen_student_form_before_creating_user(self):
        response = self.client.post(reverse("painel:students"), {
            "action":"enroll", "email":"invalido@example.test", "full_name":"Ana de Teste",
            "course_id":self.course.pk, "starts_on":"2026-09-20", "last_day":"2026-08-20",
        })
        self.assertIn("last_day", response.context["creation_form"].errors)
        self.assertContains(response, "Ana de Teste")
        self.assertFalse(User.objects.filter(email="invalido@example.test").exists())

    def test_mobile_inbox_shows_list_if_selected_topic_left_filter(self):
        post = CommunityPost.objects.create(author=self.student, title="Em atendimento", content="Texto",
                                           team_status="forwarded")
        response = self.client.get(reverse("painel:community"), {"status":"new", "topico":post.pk})
        self.assertContains(response, 'data-detail="false"')

    def test_report_kpis_use_selected_period_and_distinct_students(self):
        from users.models import StudentVisit

        StudentVisit.objects.create(student=self.student.student_profile, date=timezone.localdate()-timedelta(days=12))
        url = reverse("painel:reports")
        week = self.client.get(url, {"periodo": 7}).context["report"]
        month = self.client.get(url, {"periodo": 30}).context["report"]
        self.assertEqual((week["visiting_students"], week["inactive_current"]), (0, 1))
        self.assertEqual((month["visiting_students"], month["inactive_current"]), (1, 0))

    def test_ticket_filters_use_number_subject_and_enrolled_student(self):
        from support.models import SupportSubject, Ticket

        subject = SupportSubject.objects.create(name="Material do curso")
        ticket = Ticket.objects.create(student=self.student.student_profile, subject=subject,
                                       title="Arquivo", body="Dúvida", device="Celular", number=503)
        filters = {"q": "#503", "curso": self.course.pk, "assunto": subject.pk}
        url = reverse("painel:tickets")
        self.assertEqual(self.client.get(url, filters).context["selected"], ticket)
        filters["q"] = "learner@example.test"
        self.assertEqual(self.client.get(url, filters).context["selected"], ticket)
