"""Menu do produtor e localização da tela a partir da rota resolvida."""
from django.urls import reverse

GROUPS = (
    ("", (("dashboard", "Início", "home"),)),
    ("Conteúdo", (("courses", "Cursos", "book"), ("live", "Ao vivo", "radio"), ("certificates", "Certificados", "award"))),
    ("Alunos", (("students", "Alunos", "users"), ("expirations", "Vencimentos", "calendar"))),
    ("Atendimento", (("community", "Comunidade", "message"), ("tickets", "Chamados", "help"))),
    ("Negócio", (("reports", "Relatórios", "chart"), ("settings", "Configurações", "settings"))),
)
CHILDREN = {
    "course_new": ("courses", "Criar curso"), "course_edit": ("courses", "Detalhes"),
    "course_overview": ("courses", "Visão geral"), "course_lessons": ("courses", "Conteúdo"),
    "lesson_new": ("courses", "Nova aula"), "lesson_edit": ("courses", "Editar aula"),
    "lesson_quiz": ("courses", "Quiz"), "final_quiz": ("courses", "Avaliação final"),
    "material_cover": ("courses", "Capa do e-book"),
    "course_materials": ("courses", "Materiais"), "home_features": ("courses", "Página inicial"),
    "weekly_selection": ("courses", "Top 10 da semana"), "students_import": ("students", "Importar alunos"),
    "plan_manage": ("students", "Plano de acesso"), "support_settings": ("settings", "Central de ajuda"),
    "lesson_metrics": ("reports", "Por aula"),
}


def panel_navigation(request, counts):
    name = request.resolver_match.url_name
    section, title = CHILDREN.get(name, (name, "Ver como aluno" if name == "preview_choose" else "Painel"))
    if name == "live" and request.GET.get("curso"):
        section, title = "courses", "Ao vivo"
    groups = []
    parent = None
    for group, links in GROUPS:
        rows = []
        for route, label, icon in links:
            row = {"url": reverse("painel:" + route), "label": label, "icon": icon,
                   "active": route == section, "count": counts.get("expiring" if route == "expirations" else route, 0)}
            rows.append(row)
            if route == section:
                if name == section:
                    title = label
                else:
                    parent = row
        groups.append((group, rows))
    return {"panel_nav": groups, "panel_location": title, "panel_parent": parent}
