from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .access import module_release_date
from .models import Course, Enrollment, Lesson, LessonMaterial, Module, Progress
from users.models import User


class TrailAndLibraryTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(username="autor-trilha", role="CREATOR")
        user = User.objects.create_user(username="aluno-trilha")
        self.course = Course.objects.create(title="Urgência", slug="urgencia", creator=owner.creator_profile, is_published=True, cover_color="teal")
        self.enrollment = Enrollment.objects.create(course=self.course, student=user.student_profile, plan_started_on=timezone.localdate())
        self.first = Module.objects.create(course=self.course, title="Vias aéreas", order=1)
        self.second = Module.objects.create(course=self.course, title="Vertigem", order=1)
        self.locked = Module.objects.create(course=self.course, title="Módulo futuro", order=2, release_month=3)
        self.a = Lesson.objects.create(module=self.first, title="Primeira aula pública", order=4, duration_seconds=300)
        self.b = Lesson.objects.create(module=self.second, title="Exame da marcha", order=1, duration_seconds=600)
        self.future = Lesson.objects.create(module=self.locked, title="Título privado")
        self.extra = self.pdf(self.b, "Apêndice do material", 2)
        self.primary = self.pdf(self.b, "Caderno de leitura", 1)
        self.closed_pdf = self.pdf(self.future, "Material em agendamento", 0)
        draft = Lesson.objects.create(module=self.second, title="Rascunho de gravação", status="draft")
        self.pdf(draft, "PDF em edição", 0)
        Progress.objects.create(student=user.student_profile, lesson=self.b, last_position_seconds=180)
        self.client.force_login(user)
        self.trail = reverse("course_trail", args=[self.course.slug])
        self.library = reverse("course_ebooks", args=[self.course.slug])

    def pdf(self, lesson, title, order):
        return LessonMaterial.objects.create(lesson=lesson, title=title, order=order, url="https://example.org/book.pdf")

    def test_filter_by_theme_restricts_lessons_and_pdfs_and_preserves_global_number(self):
        response = self.client.get(self.trail, {"tema": self.second.pk})
        self.assertContains(response, "Todas as áreas")
        self.assertContains(response, "Aula 2")
        self.assertContains(response, self.b.title)
        self.assertNotContains(response, self.a.title)
        self.assertContains(response, "10 min")
        self.assertContains(response, "Em andamento · 30%")
        self.assertContains(response, "cover--teal")
        self.assertContains(response, 'class="cover__title">Exame da marcha')
        self.assertContains(response, self.primary.title)
        self.assertContains(response, self.extra.title)
        self.assertEqual(self.client.get(self.trail, {"tema": "inexistente"}).status_code, 404)

    def test_library_counts_actual_pdfs_and_displays_primary_first(self):
        response = self.client.get(self.library)
        self.assertContains(response, "Um e-book para cada aula")
        self.assertContains(response, "Os próximos chegam junto com as aulas de cada semana")
        self.assertEqual(response.context["available_books"], 2)
        self.assertEqual(response.context["total_books"], 3)
        self.assertContains(response, "Aula 2 · Exame da marcha")
        self.assertContains(response, "Material extra", count=1)
        content = response.content.decode()
        self.assertLess(content.index(self.primary.title), content.index(self.extra.title))
        for material in (self.primary, self.extra):
            self.assertContains(response, reverse("material_open", args=["lesson", material.pk])+"?download=1")
        self.assertNotContains(response, "https://example.org/book.pdf")

    def test_locked_module_is_dated_with_no_links_titles_or_materials_even_for_historical_completion(self):
        Progress.objects.create(student=self.enrollment.student, lesson=self.future, is_completed=True)
        for path in (self.trail, self.library):
            response = self.client.get(path)
            self.assertNotContains(response, "?tema="+str(self.locked.pk))
            self.assertNotContains(response, self.future.title)
            self.assertNotContains(response, self.closed_pdf.title)
            self.assertNotContains(response, reverse("lesson_detail", args=[self.course.slug, self.future.pk]))
            self.assertNotContains(response, reverse("material_open", args=["lesson", self.closed_pdf.pk]))
            self.assertNotContains(response, "PDF em edição")
        self.assertContains(self.client.get(self.trail), module_release_date(self.enrollment, self.locked).strftime("%d/%m/%Y"))

    def test_cover_falls_back_from_lesson_to_module_to_course(self):
        self.course.cover_image = "courses/base.jpg"
        self.course.save()
        self.second.cover = "modules/trilha.jpg"
        self.second.save()
        self.b.cover = "lessons/especifica.jpg"
        self.b.save()
        response = self.client.get(self.trail)
        self.assertContains(response, "lessons/especifica.jpg")
        self.assertContains(response, "courses/base.jpg")
        self.b.cover = ""
        self.b.save()
        home = self.client.get(reverse("course_home", args=[self.course.slug]))
        self.assertContains(home, "modules/trilha.jpg")
        self.assertEqual(home.context["resume"]["cover"], self.second.cover)
