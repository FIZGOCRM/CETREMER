from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from tempfile import TemporaryDirectory

from courses.models import Course, CourseMaterial, Enrollment, Lesson, LessonMaterial, MaterialOpen, Module, Quiz, QuizQuestion
from courses.services import delete_content, mark_material_open
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
        response = self.client.post(path, {"action":"publication", "status":"published"}, follow=True)
        self.assertContains(response, "Curso publicado sem aulas.")
        self.assertContains(response, "Sem aulas publicadas, o aluno vê um curso vazio.")
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

    def test_opened_pdf_protects_material_lesson_and_module_and_can_be_replaced(self):
        self.course.is_published = True
        self.course.save()
        lesson = Lesson.objects.create(title="Aula", module=self.module)
        student = User.objects.create_user(username="leitor")
        Enrollment.objects.create(student=student.student_profile, course=self.course)
        editor = reverse("painel:lesson_edit", args=[lesson.pk])
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            pdf = SimpleUploadedFile("original.pdf", b"%PDF-1.4\noriginal", content_type="application/pdf")
            fields = {"title":lesson.title, "module":self.module.pk, "duration_text":"0:00", "status":"published"}
            self.assertEqual(self.client.post(editor, {**fields, "ebook":pdf}).status_code, 302)
            material = lesson.materials.get()
            extra = LessonMaterial.objects.create(lesson=lesson, title="Extra", order=2, url="https://example.org/extra.pdf")
            self.client.force_login(student)
            self.client.get(reverse("material_open", args=["lesson", material.pk])).close()
            history = MaterialOpen.objects.get(student=student.student_profile, material_id=material.pk)
            self.client.force_login(self.creator)
            self.assertEqual(self.client.post(editor, {"action":"remove_material", "material_id":material.pk}).status_code, 400)
            self.assertTrue(lesson.materials.filter(pk=material.pk).exists())
            self.assertContains(self.client.get(editor), "Substituir o primeiro PDF")
            self.assertNotContains(self.client.get(editor), 'value="remove_material"')
            self.client.post(editor, {"action":"delete"})
            self.client.post(self.url("course_lessons"), {"action":"delete_module", "module_id":self.module.pk})
            self.assertTrue(Lesson.objects.filter(pk=lesson.pk).exists())
            self.assertTrue(Module.objects.filter(pk=self.module.pk).exists())
            replacement = SimpleUploadedFile("novo.pdf", b"%PDF-1.4\nnovo", content_type="application/pdf")
            self.assertEqual(self.client.post(editor, {**fields, "ebook":replacement}).status_code, 302)
            extra.refresh_from_db()
            self.assertEqual(extra.url, "https://example.org/extra.pdf")
            material.refresh_from_db()
            self.assertEqual(material.title, "novo.pdf")
            self.assertEqual(MaterialOpen.objects.get().pk, history.pk)

    def test_replacement_rejects_invalid_uploads_and_material_from_another_lesson(self):
        lesson = Lesson.objects.create(title="Aula", module=self.module)
        other = Lesson.objects.create(title="Outra", module=self.module)
        editor = reverse("painel:lesson_edit", args=[lesson.pk])
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media, MATERIAL_MAX_MB=1):
            material = LessonMaterial.objects.create(lesson=lesson, title="Original", url="https://example.org/original.pdf")
            foreign = LessonMaterial.objects.create(lesson=other, title="De outra aula", url="https://example.org/extra.pdf")
            for filename, content, mime in [
                ("a.txt", b"%PDF-1.4", "application/pdf"), ("a.pdf", b"texto", "application/pdf"),
                ("a.pdf", b"%PDF-1.4", "text/html"), ("a.pdf", b"%PDF-" + bytes(1024 * 1024), "application/pdf"),
            ]:
                with self.subTest(filename=filename, mime=mime, size=len(content)):
                    fields = {"title":lesson.title, "module":self.module.pk, "duration_text":"0:00", "status":"published"}
                    response = self.client.post(editor, {**fields, "ebook":SimpleUploadedFile(filename, content, content_type=mime)})
                    self.assertEqual(response.status_code, 200)
                    material.refresh_from_db()
                    self.assertEqual(material.title, "Original")
                    self.assertFalse(material.file)
            for action in ("remove_material", "replace_material", "add_material"):
                self.assertEqual(self.client.post(editor, {"action":action, "material_id":foreign.pk}).status_code, 400)
            self.assertTrue(other.materials.filter(pk=foreign.pk).exists())
            self.assertTrue(lesson.materials.filter(pk=material.pk).exists())

    def test_first_open_arriving_after_lesson_deletion_cannot_create_orphan_history(self):
        lesson = Lesson.objects.create(title="Aula sem histórico", module=self.module)
        material = LessonMaterial.objects.create(lesson=lesson, title="Documento", url="https://example.org/arquivo.pdf")
        delete_content(lesson, actor=self.creator)
        student = User.objects.create_user(username="leitor-tardio")
        self.assertIsNone(mark_material_open(student.student_profile, "lesson", material.pk))
        self.assertFalse(MaterialOpen.objects.filter(material_kind="lesson", material_id=material.pk).exists())
