import csv
from django.http import HttpResponse
from core.decorators import painel_required
from core.csv_export import safe_csv_cell
from painel.reporting import report_data
from painel.reporting import lesson_metrics
from painel.analytics_forms import LessonMetricsForm
from .common import page


def _period(request):
    raw=request.GET.get('dias','7')
    return int(raw) if raw in ('7','30','90') else 7

@painel_required
def reports(request):
    return page(request,'reports',report=report_data(days=_period(request)))


@painel_required
def lesson_report(request):
    data = request.GET.copy()
    data.setdefault('dias', 'tudo')
    data.setdefault('ordem', '-started')
    form = LessonMetricsForm(data)
    rows = []
    if form.is_valid():
        filters = form.cleaned_data
        days = None if filters['dias'] == 'tudo' else int(filters['dias'])
        rows = lesson_metrics(course=filters['curso'], days=days, order=filters['ordem'])
    return page(request, 'lesson_metrics', form=form, rows=rows)

@painel_required
def export_reports(request):
    report=report_data(days=_period(request))
    response=HttpResponse(content_type='text/csv; charset=utf-8');response['Content-Disposition']='attachment; filename="relatorios-gomut.csv"';response.write('\ufeff')
    writer=csv.writer(response,delimiter=';')
    def row(*values):writer.writerow([safe_csv_cell(value) for value in values])
    row('Tipo','Curso','Aluno','Data','Indicador','Valor')
    row('Resumo','','',report['today'],'Alunos com acesso registrado em 7 dias',report['active_7'])
    row('Resumo','','',report['today'],f'Segundos de estudo em {report["days"]} dias',report['study_seconds'])
    for item in report['visits']:row('Acessos','','',item['date'],'Alunos distintos',item['count'])
    for item in report['courses']:
        row('Curso',item['course'].title,'','','Progresso médio (%)',item['progress_pct'])
        row('Curso',item['course'].title,'','','Aprovação final (%)',item['approval_pct'])
    for lesson in report['top_lessons']:row('Aula',lesson.module.course.title,'','',lesson.title,lesson.completions)
    for student in report['inactive']:row('Sem acesso recente','',student.full_name or student.user.email,student.last_seen,'Último acesso diário registrado','')
    for item in report['expiring']:row('Vencimento',item['enrollment'].course.title,item['enrollment'].student.full_name or item['enrollment'].student.user.email,item['plan']['last_day'],'Progresso (%)',item['pct'])
    return response
