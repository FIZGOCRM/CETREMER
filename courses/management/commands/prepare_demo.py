"""Opt-in, non-destructive fixture for the local member demonstration."""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from courses.models import AccessPeriod, Category, Course, Enrollment, Lesson, Module
from users.models import User


class Command(BaseCommand):
    help = "Cria dois cursos e acessos fictícios; exige GOMUT_DEMO_MODE=True. Não apaga dados."

    def add_arguments(self, parser):
        parser.add_argument("--password", required=True, help="Senha apenas para novas contas de demonstração.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.GOMUT_DEMO_MODE:
            raise CommandError("Prepare uma base de demonstração separada e habilite GOMUT_DEMO_MODE.")
        password = options["password"]
        from users.models import SiteSettings
        site, _ = SiteSettings.objects.get_or_create(pk=1, defaults={'school_name':'Emergensimples', 'email_from_name':'Emergensimples'})
        if site.school_name == 'CETREMER':
            site.school_name = 'Emergensimples'
            site.save(update_fields=['school_name'])
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        admin, created = User.objects.get_or_create(username="gomut-demo-admin", defaults={
            "email": "admin@gomut.example", "role": User.Role.CREATOR, "is_staff": True,
        })
        if created:
            admin.set_password(password)
            admin.save(update_fields=["password"])
        if not hasattr(admin, "creator_profile"):
            raise CommandError("O identificador de demonstração já pertence a outro perfil.")
        student, created = User.objects.get_or_create(username="gomut-demo-student", defaults={
            "email": "aluno@gomut.example", "role": User.Role.STUDENT,
        })
        if created:
            student.set_password(password)
            student.save(update_fields=["password"])
            student.student_profile.full_name = "Marina Souza · Demonstração"
            student.student_profile.save()
        if student.role != User.Role.STUDENT:
            raise CommandError("O identificador de demonstração já pertence a outro perfil.")
        category, _ = Category.objects.get_or_create(slug="gomut-demo-emergencia", defaults={"name": "Emergência", "color": "teal"})
        courses = [
            ("plantao", "Plantão sem GPT", "Raciocínio clínico passo a passo e organização do atendimento em emergência."),
            ("cardiologia", "Emergências cardiovasculares", "Fundamentos de avaliação, ECG e discussão de situações clínicas. Conteúdo fictício para demonstração."),
        ]
        today = timezone.localdate()
        for slug, title, description in courses:
            course, _ = Course.objects.get_or_create(slug="gomut-demo-"+slug, defaults={
                "title": title, "description": description, "creator": admin.creator_profile,
                "category": category, "is_published": True,
            })
            for n, module_title in enumerate(["Fundamentos", "Discussão de casos"], 1):
                module, _ = Module.objects.get_or_create(course=course, order=n, defaults={"title": module_title})
                for order, lesson_title in enumerate(["Introdução ao atendimento", "Aplicação prática"], 1):
                    Lesson.objects.get_or_create(module=module, order=order, defaults={
                        "title": lesson_title, "description": "Aula fictícia. O player utiliza um vídeo público de demonstração do Vimeo, sem conteúdo clínico deste curso.",
                        "video_url": "https://vimeo.com/76979871", "duration_seconds": 62,
                    })
            enrollment, _ = Enrollment.objects.get_or_create(student=student.student_profile, course=course,
                defaults={"access_policy": Enrollment.AccessPolicy.PERIODS})
            AccessPeriod.objects.get_or_create(enrollment=enrollment, source="manual", reference="gomut-demo-initial", defaults={
                "starts_on": today, "ends_on": today+timedelta(days=30), "grace_days": 3, "created_by": admin,
            })
            from courses.demo_quizzes import DEMO_LESSON_QUESTIONS
            from courses.models import Quiz
            from courses.services import save_quiz_question
            first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id').first()
            quiz, new_quiz = Quiz.objects.get_or_create(lesson=first_lesson, defaults={'course': course, 'kind': 'lesson', 'is_demo': True})
            if new_quiz:
                for index, (text, choices, correct, explanation) in enumerate(DEMO_LESSON_QUESTIONS[slug], 1):
                    save_quiz_question(quiz, order=index, text=text, explanation=explanation, choices=choices, correct_index=correct, actor=admin)
            from courses.demo_quizzes import DEMO_FINAL_QUESTIONS
            final, new_final = Quiz.objects.get_or_create(course=course, kind='final', defaults={'is_demo':True})
            if new_final:
                for index, (text, choices, correct) in enumerate(DEMO_FINAL_QUESTIONS[slug], 1):
                    save_quiz_question(final, order=index, text=text, explanation='', choices=choices, correct_index=correct, actor=admin)
            from django.core.files.base import ContentFile
            from courses.demo_materials import demo_pdf_bytes
            from courses.models import CourseMaterial, LessonMaterial
            CourseMaterial.objects.get_or_create(course=course, title='Material ilustrativo do curso', defaults={'file':ContentFile(demo_pdf_bytes(),name='demonstracao-curso.pdf'),'order':1})
            LessonMaterial.objects.get_or_create(lesson=first_lesson, title='Material ilustrativo da aula', defaults={'file':ContentFile(demo_pdf_bytes(),name='demonstracao-aula.pdf'),'order':1})
        from users.models import SiteSettings
        site=SiteSettings.load()
        for field,value in {'mentor_display_name':'Mentor da Emergensimples','mentor_label':'Mentor','team_display_name':'Equipe Emergensimples'}.items():
            if not getattr(site,field):setattr(site,field,value)
        site.save()
        from community.models import CommunityPost
        for course in Course.objects.filter(slug__in=['gomut-demo-plantao','gomut-demo-cardiologia']):
            CommunityPost.objects.get_or_create(course=course,author=student,title='Como organizar a revisão deste curso?',defaults={'content':'Tópico fictício para conhecer a comunidade. Como vocês organizam a revisão das aulas?'})
        self.stdout.write(self.style.SUCCESS("Demonstração preparada: dois cursos; aluno@gomut.example e admin@gomut.example. Senhas existentes foram preservadas."))
