from django import forms


class LessonNoteForm(forms.Form):
    position_seconds = forms.IntegerField(min_value=0)
    text = forms.CharField(strip=True)


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
