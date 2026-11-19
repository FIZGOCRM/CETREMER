from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from tempfile import TemporaryDirectory

from courses.models import Course, CourseMaterial, Lesson, Module, Quiz, QuizQuestion
from users.models import User


class CourseHandoffTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="designer", role="CREATOR")
        self.client.force_login(self.creator)
        self.course = Course.objects.create(title="Curso", slug="curso", creator=self.creator.creator_profile)
        self.module = Module.objects.create(title="Primeiro", course=self.course)

    def url(self, name):
        return reverse("painel:" + name, args=[self.course.pk])

    def test_attention_uses_publication_of_both_module_and_lesson(self):
        self.course.is_published = True
        self.course.save()
        self.module.status = "draft"
        self.module.save()
        Lesson.objects.create(module=self.module, title="A", status="published")
        response = self.client.get(reverse("painel:courses"), {"visao": "atencao"})
        self.assertContains(response, "Publicado sem aulas")
        self.module.status = "published"
        self.module.save()
        response = self.client.get(reverse("painel:courses"), {"visao": "atencao"})
        self.assertContains(response, "Nenhum curso encontrado")

    def test_publication_is_independent_of_details(self):
        path = self.url("course_edit")
        self.client.post(path, {"action": "publication", "status": "published"})
        self.course.refresh_from_db()
        self.assertFalse(self.course.is_published)
        Lesson.objects.create(module=self.module, title="A", status="published")
        self.client.post(path, {"action": "publication", "status": "published"})
        self.course.refresh_from_db()
        self.assertTrue(self.course.is_published)
        self.client.post(path, {"action": "details", "title": "Novo nome", "plan_months": 12})
        self.course.refresh_from_db()
        self.assertTrue(self.course.is_published)
        self.assertEqual(self.course.title, "Novo nome")

    def test_new_lesson_preselects_module_within_course(self):
        response = self.client.get(self.url("lesson_new"), {"modulo": self.module.pk})
        self.assertEqual(str(response.context["form"]["module"].value()), str(self.module.pk))

    def test_weekly_editor_has_ten_slots_and_metrics_link(self):
        response = self.client.get(self.url("weekly_selection"))
        self.assertContains(response, "data-ranking-slot", count=10)
        self.assertContains(response, "Preencher pelo engajamento")
        self.assertNotContains(response, "Métricas acumuladas das aulas")

    def test_question_reorder_rejects_foreign_or_partial_lists(self):
        quiz = Quiz.objects.create(kind="final", course=self.course)
        first, second = [QuizQuestion.objects.create(quiz=quiz, order=i, text=f"Pergunta {i}") for i in (1, 2)]
        path = self.url("final_quiz")
        for ids in [[str(second.pk)], [str(second.pk), str(second.pk)], ["9999", str(first.pk)]]:
            self.assertEqual(self.client.post(path, {"ids": ids}, content_type="application/json").status_code, 409)
        response = self.client.post(path, {"ids": [str(second.pk), str(first.pk)]}, content_type="application/json")
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(list(quiz.questions.values_list("pk", flat=True)), [second.pk, first.pk])

    def test_bulk_upload_validates_every_pdf_before_persistence(self):
        path = self.url("course_materials")
        def pdf(name, content=b"%PDF-1.4\n%%EOF"):
            return SimpleUploadedFile(name, content, content_type="application/pdf")
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            result = self.client.post(path, {"action": "upload", "pdfs": [pdf("one.pdf"), pdf("bad.pdf", b"bad")]})
            self.assertContains(result, "O arquivo precisa ser um PDF válido")
            self.assertFalse(CourseMaterial.objects.exists())
            self.assertRedirects(self.client.post(path, {"action": "upload", "pdfs": [pdf("one.pdf"), pdf("two.pdf")]}), path)
            first, second = self.course.materials.all()
            self.assertEqual(self.client.post(path, {"ids":[str(second.pk), str(first.pk)]}, content_type="application/json").status_code, 200)
            self.assertEqual(list(self.course.materials.values_list("title", flat=True)), ["two.pdf", "one.pdf"])
