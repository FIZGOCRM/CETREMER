from django import forms
from django.core.validators import FileExtensionValidator

from core.deploy_media import PUBLIC_IMAGE_EXTENSIONS
from courses.models import Course
from .reporting import LESSON_SORTS


class CardArtworkField(forms.ImageField):
    default_validators = [FileExtensionValidator(PUBLIC_IMAGE_EXTENSIONS)]


class LessonMetricsForm(forms.Form):
    curso = forms.ModelChoiceField(required=False, label='Curso', empty_label='Todos os cursos',
                                   queryset=Course.objects.order_by('title', 'pk'))
    dias = forms.ChoiceField(label='Início da aula', choices=[
        ('tudo', 'Todo o histórico'), ('7', 'Últimos 7 dias'), ('30', 'Últimos 30 dias'),
    ])
    ordem = forms.ChoiceField(label='Ordenar por', choices=[
        (prefix + key, f'{label} · {direction}')
        for key, label in LESSON_SORTS
        for prefix, direction in [('-', 'decrescente'), ('', 'crescente')]
    ])


class WeekForm(forms.Form):
    semana = forms.DateField(label='Segunda-feira da semana', input_formats=['%Y-%m-%d'],
                             widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    def clean_semana(self):
        week = self.cleaned_data['semana']
        if week.weekday() != 0:
            raise forms.ValidationError('Escolha a segunda-feira da semana desejada.')
        return week


class WeeklySelectionForm(WeekForm):
    def __init__(self, *args, rows, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semana'].widget = forms.HiddenInput()
        choices = [('', 'Sem aula nesta posição')]
        for row in rows:
            lesson = row['lesson']
            label = f'{lesson.module.title} / {lesson.title} · {row["started"]} iniciaram'
            if row['finish_pct'] is not None:
                label += f' · {row["finish_pct"]:.0f}% chegaram ao final'
            choices.append((lesson.pk, label))
        for position in range(1, 11):
            self.fields[f'lesson_{position}'] = forms.ChoiceField(
                label=f'{position}º lugar', required=False, choices=choices,
            )
            self.fields[f'art_{position}'] = CardArtworkField(
                label=f'Arte do {position}º lugar (pôster 2:3)', required=False,
            )

    def clean(self):
        data = super().clean()
        if any(name.startswith('lesson_') and name not in self.fields for name in self.data):
            raise forms.ValidationError('Escolha no máximo dez posições, numeradas de 1 a 10.')
        positions = {}
        for position in range(1, 11):
            name = f'lesson_{position}'
            if value := data.get(name):
                if int(value) in positions.values():
                    self.add_error(name, 'Esta aula já ocupa outra posição.')
                positions[position] = int(value)
        data['positions'] = positions
        for position in range(1, 11):
            key = f'art_{position}'
            if key in self.files and position not in positions:
                self.add_error(key, 'Escolha a aula desta posição.')
        return data
