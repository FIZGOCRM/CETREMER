from django import forms
from users.validators import validate_cpf


class CertificateDataForm(forms.Form):
    full_name = forms.CharField(max_length=200, label='Nome completo', widget=forms.TextInput(attrs={'class':'input'}))
    cpf = forms.CharField(required=False, label='CPF', widget=forms.PasswordInput(render_value=False, attrs={'type':'text', 'inputmode':'numeric', 'class':'input', 'autocomplete':'off'}))

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        kwargs.setdefault('initial', {'full_name':profile.full_name or ''})
        super().__init__(*args, **kwargs)

    def clean_cpf(self):
        return validate_cpf(self.cleaned_data.get('cpf') or self.profile.cpf or '')


class LessonNoteForm(forms.Form):
    position_seconds = forms.IntegerField(min_value=0)
    text = forms.CharField(strip=True)


class QuizAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    choice_id = forms.IntegerField(min_value=1)


class HeartbeatForm(forms.Form):
    position = forms.FloatField(min_value=0)
    playing = forms.BooleanField(required=False)

    def clean_position(self):
        if isinstance(self.data.get('position'), bool):
            raise forms.ValidationError('Posição do vídeo inválida.')
        return self.cleaned_data['position']

    def clean_playing(self):
        if not isinstance(self.data.get('playing'), bool):
            raise forms.ValidationError('Informe se o vídeo está tocando.')
        return self.cleaned_data['playing']
