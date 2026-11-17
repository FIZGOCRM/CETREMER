from django import forms
from courses.models import LiveEvent

class LiveEventForm(forms.ModelForm):
    class Meta:
        model=LiveEvent
        fields=['course','title','kind','starts_at','duration_minutes','description','room_url','recording_url','is_active']
        labels={'course':'Curso (vazio: todos os alunos ativos)','title':'Título','kind':'Tipo','starts_at':'Início (horário da plataforma)','duration_minutes':'Duração em minutos','description':'Descrição','room_url':'Link da sala','recording_url':'Link da gravação','is_active':'Ativo'}
        widgets={'starts_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M',attrs={'type':'datetime-local'})}
