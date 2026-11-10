import os
import django

# Setup Django environment settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from datetime import timedelta

from django.utils import timezone

from community.models import Comment, CommunityPost
from core.activity import log
from core.models import ActivityLog
from users.models import CreatorProfile, StudentProfile, SiteSettings, Notification
from courses.models import Category, Certificate, Course, Module, Lesson, LessonMaterial, Enrollment, HeroBanner, LiveSession, Progress

User = get_user_model()

def create_seed_data():
    print("Clearing old course and user data...")
    # Clear database state
    ActivityLog.objects.all().delete()
    Certificate.objects.all().delete()
    User.objects.all().delete()
    Course.objects.all().delete()
    Category.objects.all().delete()

    essentials = Category.objects.create(name="Essenciais AHA", slug="essenciais-aha", color="blue", order=1)
    specialties = Category.objects.create(name="Especialidades médicas", slug="especialidades-medicas", color="teal", order=2)
    leigos = Category.objects.create(name="Para leigos", slug="para-leigos", color="slate", order=3)
    
    print("Creating mock user credentials...")
    # 1. Create a demo creator user with profile trigger
    creator_user = User.objects.create_user(
        username="john_creator",
        email="john@creator.com",
        password="password123",
        role=User.Role.CREATOR
    )
    creator_profile = creator_user.creator_profile
    creator_profile.company_name = "Tech Academy Inc."
    creator_profile.save()
    
    # 2. Create a demo student user with profile trigger
    student_user = User.objects.create_user(
        username="jane_student",
        email="jane@student.com",
        password="password123",
        role=User.Role.STUDENT
    )

    # 3. Create a Django admin superuser account
    admin_user = User.objects.create_superuser(
        username="admin",
        email="admin@cetremer.com.br",
        password="password123",
        role=User.Role.ADMIN
    )
        
    print("Pre-registered accounts ready:")
    print("  Student Profile: username='jane_student' password='password123'")
    print("  Creator Profile: username='john_creator' password='password123'")
    print("  Admin Superuser: username='admin' password='password123'")

    # 3. Create mockup courses
    c1 = Course.objects.create(
        title="BLS - Suporte Básico de Vida",
        slug="suporte-basico-vida-bls",
        description="Curso presencial credenciado pela American Heart Association (AHA). Aprenda RCP de alta qualidade, manobras de desengasgo e uso do Desfibrilador Externo Automático (DEA).",
        category=essentials, short_name="BLS", cover_color="blue", workload_hours=8,
        creator=creator_profile,
        price=150.00,
        status='published',
        cover_image="courses/bls_cover.png"
    )
    
    c2 = Course.objects.create(
        title="ACLS - Suporte Avançado de Vida em Cardiologia",
        slug="suporte-avancado-cardiologia-acls",
        description="Curso avançado credenciado pela AHA. Focado em atendimento emergencial cardiovascular, RCP de alto desempenho, ritmos de PCR e dinâmica de equipe médica.",
        category=essentials, short_name="ACLS", cover_color="blue-2", workload_hours=16,
        creator=creator_profile,
        price=450.00,
        status='published',
        cover_image="courses/acls_cover.png"
    )
    
    c3 = Course.objects.create(
        title="PALS - Suporte Avançado de Vida em Pediatria",
        slug="suporte-avancado-pediatria-pals",
        description="Curso avançado pediátrico credenciado pela AHA. Manejo de paradas cardíacas, insuficiência respiratória e choque em crianças e neonatos.",
        category=specialties, short_name="PALS", cover_color="teal", workload_hours=16,
        creator=creator_profile,
        price=500.00,
        status='published',
        cover_image="courses/pals_cover.png"
    )
    
    c4 = Course.objects.create(
        title="DEA e Primeiros Socorros para Leigos",
        slug="dea-primeiros-socorros-leigos",
        description="Treinamento prático direcionado a escolas, empresas, brigadas de incêndio e cidadãos que desejam aprender a salvar vidas e utilizar o DEA no dia a dia.",
        category=leigos, short_name="DEA", cover_color="slate", workload_hours=4,
        creator=creator_profile,
        price=90.00,
        status='published',
        cover_image="courses/dea_cover.png"
    )
    
    c5 = Course.objects.create(
        title="Plantão Sem GPT",
        slug="plantao-sem-gpt",
        description="O guia prático definitivo para médicos dominarem condutas de emergência, UTI e pronto-socorro de forma rápida e segura na vida real, sem depender de GPT ou consultas rápidas.",
        category=specialties, short_name="Plantão", cover_color="ink",
        creator=creator_profile,
        price=190.00,
        status='published',
        cover_image="courses/plantao_cover.png",
        live_meet_url="https://meet.google.com/abc-defg-hij",
        live_schedule_embed='<iframe src="https://calendar.google.com/calendar/embed?src=pt.brazilian%23holiday%40group.v.calendar.google.com&ctz=America%2FCampo_Grande" style="border: 0" width="100%" height="320" frameborder="0" scrolling="no"></iframe>'
    )
    
    print("Created mock courses.")

    # 4. Create modules & lessons for BLS
    m1 = Module.objects.create(course=c1, title="Introdução ao Suporte Básico", order=1)
    bls_lesson_1 = first_lesson = Lesson.objects.create(
        module=m1,
        title="Reconhecimento da PCR e Corrente de Sobrevivência",
        description="Nesta aula inicial, cobriremos o diagnóstico rápido de uma parada cardiorrespiratória e a cadeia de sobrevivência intra e extra-hospitalar.",
        video_url="https://vimeo.com/76979871",
        duration_seconds=300,
        order=1,
    )
    LessonMaterial.objects.create(
        lesson=first_lesson,
        title="AHA BLS Algoritmo de PCR em Adultos (PDF)",
        url="https://www.heart.org/-/media/files/providers/handbook-resources/bls-adult-cardiac-arrest-algorithm-pdf.pdf",
    )
    bls_lesson_2 = Lesson.objects.create(
        module=m1,
        title="Compressões Torácicas em Adultos",
        description="Treinamento prático de posicionamento, frequência (100 a 120 por minuto) e profundidade (5 a 6 cm) recomendadas pela AHA.",
        video_url="https://vimeo.com/76979871",
        duration_seconds=420,
        order=2
    )

    m2 = Module.objects.create(course=c1, title="Desfibrilação e Técnicas Especiais", order=2)
    Lesson.objects.create(
        module=m2,
        title="Operação e Segurança do DEA",
        description="Como ligar, posicionar as pás e aplicar o choque de segurança utilizando o desfibrilador externo automático em adultos e crianças.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=500,
        order=3
    )
    Lesson.objects.create(
        module=m2,
        title="Manejo de Engasgo (Obstrução de Vias Aéreas)",
        description="Aprenda a aplicar a Manobra de Heimlich em adultos conscientes e os protocolos de intervenção em bebês e gestantes.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=460,
        order=4
    )

    # Aula em rascunho: não aparece para o aluno nem entra nas contagens de progresso.
    Lesson.objects.create(
        module=m2,
        title="Simulado final (em preparação)",
        description="Aula ainda não publicada.",
        duration_seconds=0,
        order=5,
        status="draft",
    )

    # Create module & lesson for ACLS
    m3 = Module.objects.create(course=c2, title="Reconhecimento e Fármacos do ACLS", order=1)
    Lesson.objects.create(
        module=m3,
        title="Dinâmica de Equipe de Alto Desempenho",
        description="Entenda os papéis de liderança, comunicação em alça fechada e organização de equipes na sala de emergência médica.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=360,
        order=1
    )

    # Create module & lesson for PALS (c3)
    m_pals = Module.objects.create(course=c3, title="Emergências Pediátricas e RCP", order=1)
    Lesson.objects.create(
        module=m_pals,
        title="Reconhecimento de Insuficiência Respiratória Pediátrica",
        description="Diretrizes da AHA para diagnosticar e intervir em paradas ou falências respiratórias infantis.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=420,
        order=1
    )

    # Create module & lesson for DEA Leigos (c4)
    m_dea = Module.objects.create(course=c4, title="RCP e Uso do DEA para Leigos", order=1)
    Lesson.objects.create(
        module=m_dea,
        title="Engasgo e Obstrução de Vias Aéreas para Leigos",
        description="Como realizar compressões de socorro e manobra de desengasgo em ambientes escolares ou de trabalho.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=380,
        order=1
    )

    # Create module & lesson for Plantão Sem GPT (c5)
    m4 = Module.objects.create(course=c5, title="Condutas Imediatas", order=1)
    plantao_lesson = Lesson.objects.create(
        module=m4,
        title="Manejo da Via Aérea Difícil e Intubação",
        description="Passo a passo prático para intubação orotraqueal em cenários críticos na sala de emergência.",
        video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        duration_seconds=480,
        order=1
    )
    
    print("Created mock modules and lessons.")

    # 5. Create default enrollments
    Enrollment.objects.create(
        student=student_user.student_profile,
        course=c1
    )
    Enrollment.objects.create(
        student=student_user.student_profile,
        course=c5
    )
    
    # 5b. Dados para conferir todas as telas do v2 sem criar nada à mão (HANDOFF-v2 6.6)
    jane = student_user.student_profile
    now = timezone.now()

    # Jane: BLS em andamento (1 de 4 publicadas, posição salva de 192 s na aula 2) e Plantão concluído sem certificado.
    Progress.objects.create(student=jane, lesson=bls_lesson_1, is_completed=True)
    Progress.objects.create(student=jane, lesson=bls_lesson_2, is_completed=False, position_seconds=192)
    Progress.objects.create(student=jane, lesson=plantao_lesson, is_completed=True)
    Enrollment.objects.filter(student=jane).update(last_accessed_at=now - timedelta(hours=1))

    # Dois alunos que nunca acessaram (matriculados, sem primeiro acesso).
    for number in (1, 2):
        never = User.objects.create_user(username="nunca%d" % number, email="nunca%d@student.com" % number, role=User.Role.STUDENT)
        never.set_unusable_password()
        never.save()
        never.student_profile.full_name = "Aluno Sem Acesso %d" % number
        never.student_profile.save()
        Enrollment.objects.create(student=never.student_profile, course=c1, source="import")

    # Plantão Sem GPT: 3 encontros futuros e 2 passados com gravação.
    for days, title in ((-14, "Encontro 1: via aérea difícil"), (-7, "Encontro 2: choque e vasopressores")):
        starts = (now + timedelta(days=days)).replace(hour=23, minute=0, second=0, microsecond=0)
        LiveSession.objects.create(
            course=c5, title=title, starts_at=starts, ends_at=starts + timedelta(hours=1, minutes=30),
            host_name="Dr. Rafael Souza", recording_url="https://vimeo.com/76979871",
            recording_until=(starts + timedelta(days=30)).date(),
        )
    for days, title in ((2, "Encontro 3: casos de sala vermelha"), (9, "Encontro 4: sedação e analgesia"), (16, "Encontro 5: pós-parada")):
        starts = (now + timedelta(days=days)).replace(hour=23, minute=0, second=0, microsecond=0)
        LiveSession.objects.create(
            course=c5, title=title, starts_at=starts, ends_at=starts + timedelta(hours=1, minutes=30),
            host_name="Dr. Rafael Souza", meet_url="https://meet.google.com/abc-defg-hij",
        )

    # Comunidade: 4 dúvidas (2 respondidas por instrutor, 1 sem resposta, 1 geral).
    q1 = CommunityPost.objects.create(author=student_user, course=c1, lesson=bls_lesson_2,
                                      title="Profundidade da compressão", content="Em 02:40, qual a profundidade correta em adultos?")
    q2 = CommunityPost.objects.create(author=student_user, course=c1, lesson=bls_lesson_1,
                                      title="Diferença entre PCR e infarto", content="Ainda não ficou claro como diferenciar no primeiro atendimento.")
    CommunityPost.objects.create(author=student_user, course=c5, lesson=plantao_lesson,
                                 title="Material complementar da aula", content="Há algum artigo recomendado sobre intubação em sequência rápida?")
    CommunityPost.objects.create(author=student_user, title="Como funcionam os certificados?",
                                 content="O certificado sai automaticamente quando eu terminar todas as aulas?")
    Comment.objects.create(post=q1, author=creator_user, content="De 5 a 6 cm, com retorno completo do tórax entre as compressões.")
    Comment.objects.create(post=q2, author=creator_user, content="Na PCR não há pulso nem respiração normal. No infarto a pessoa responde.")

    # Avisos: 3 não lidos para Jane.
    Notification.objects.create(user=student_user, kind="answer", title="O instrutor respondeu sua dúvida",
                                meta="BLS · Profundidade da compressão", url="/community/?duvida=%d" % q1.id)
    Notification.objects.create(user=student_user, kind="live", title="Aula ao vivo em 2 dias",
                                meta="Plantão Sem GPT · Encontro 3: casos de sala vermelha", url="/ao-vivo/")
    Notification.objects.create(user=student_user, kind="certificate", title="Seu certificado está pronto para emitir",
                                meta="Plantão Sem GPT · confira nome e CPF", url="/certificados/?emitir=%s" % c5.slug)

    # Atividade recente (painel e ficha do aluno).
    log("enrolled", "Jane Student foi matriculada em BLS", actor=admin_user, student=student_user, course=c1)
    log("enrolled", "Jane Student foi matriculada em Plantão Sem GPT", actor=admin_user, student=student_user, course=c5)
    log("completed_lesson", "Jane Student concluiu a aula 1 do BLS", student=student_user, course=c1)

    # 6. Seed Hero Banner
    HeroBanner.objects.all().delete()
    HeroBanner.objects.create(
        title="Torne-se preparado para salvar vidas em situações reais",
        subtitle="Capacitação e simulação realística ministrada por médicos atuantes no SAMU e sala vermelha. Aprenda na prática a conduzir emergências cardiovasculares e suporte básico de vida.",
        primary_button_text="Explorar Cursos",
        primary_button_url="#catalog",
        whatsapp_button_text="Falar pelo WhatsApp",
        whatsapp_button_url="https://wa.me/5567996494740",
        is_active=True
    )

    SiteSettings.objects.update_or_create(pk=1, defaults={
        'school_name': 'CETREMER',
        'whatsapp': '5567996494740',
        'gateway_name': 'MOCK_GATEWAY',
    })
    
    print("Created default student course enrollments and Hero Banner.")
    print("\nDatabase seeded successfully!")

if __name__ == '__main__':
    create_seed_data()
