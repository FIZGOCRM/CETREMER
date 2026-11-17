"""Input contracts for management workflows."""

from urllib.parse import urlparse
from datetime import date

from django import forms

from courses.models import Course, Lesson, Module


class AccessPeriodForm(forms.Form):
    starts_on = forms.DateField(input_formats=["%Y-%m-%d"])
    paid_through = forms.DateField(input_formats=["%Y-%m-%d"])
    reference = forms.UUIDField()
    confirm_periods = forms.BooleanField(required=True)

    def clean(self):
        data = super().clean()
        start, last = data.get("starts_on"), data.get("paid_through")
        if start and last and last < start:
            raise forms.ValidationError("O último dia quitado deve ser igual ou posterior ao início.")
        if last == date.max:
            raise forms.ValidationError("Informe uma data final anterior a 31/12/9999.")
        return data


class PlanForm(forms.Form):
    action = forms.ChoiceField(choices=[(v, v) for v in ('create', 'end', 'reactivate', 'correct', 'note')])
    starts_on = forms.DateField(required=False)
    last_day = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    reason_code = forms.ChoiceField(required=False, choices=[('', 'Escolha'), ('withdrawal', 'Desistência'), ('nonpayment', 'Inadimplência'), ('student_request', 'Pedido do aluno'), ('other', 'Outro')])
    reason_text = forms.CharField(required=False)
    admin_note = forms.CharField(required=False)

    def clean(self):
        data = super().clean()
        required = {'create': ['starts_on'], 'correct': ['starts_on', 'last_day', 'reason_text'], 'end': ['end_date', 'reason_code'], 'reactivate': ['last_day']}
        for field in required.get(data.get('action'), []):
            if not data.get(field):
                self.add_error(field, 'Preencha este campo.')
        if data.get('last_day') == date.max:
            self.add_error('last_day', 'Informe uma data anterior a 31/12/9999.')
        return data


class CourseForm(forms.ModelForm):
    plan_months = forms.IntegerField(min_value=1, required=False, initial=12)
    price = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )

    class Meta:
        model = Course
        fields = [
            'plan_months',
            "title",
            "description",
            "category",
            "short_name",
            "cover_color",
            "workload_hours",
            "price",
            "learning_objectives",
            "target_audience",
            "live_meet_url",
            "live_calendar_url",
            "is_published",
            "cover_image",
        ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("auto_id", "%s")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                continue
            widget.attrs["class"] = (
                "textarea"
                if isinstance(widget, forms.Textarea)
                else "select"
                if isinstance(widget, forms.Select)
                else "input"
            )

    def clean_price(self):
        return self.cleaned_data["price"] or 0

    def clean_plan_months(self):
        return self.cleaned_data['plan_months'] or 12

    def clean_live_calendar_url(self):
        url = self.cleaned_data["live_calendar_url"]
        if url and urlparse(url).hostname != "calendar.google.com":
            raise forms.ValidationError("Use o link público de uma agenda do Google.")
        return url


class LessonForm(forms.ModelForm):
    status = forms.ChoiceField(choices=[('draft', 'Rascunho'), ('published', 'Publicado')], required=False)
    duration_minutes = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = Lesson
        fields = ["module", "title", "description", "video_url", 'status']

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["module"].queryset = Module.objects.filter(course=course)

    def clean_video_url(self):
        url = self.cleaned_data["video_url"]
        if url and urlparse(url).hostname not in {
            "vimeo.com",
            "www.vimeo.com",
            "player.vimeo.com",
            "youtube.com",
            "www.youtube.com",
            "youtu.be",
        }:
            raise forms.ValidationError("Use um link do Vimeo ou YouTube.")
        return url

    def clean_status(self):
        return self.cleaned_data['status'] or self.instance.status or 'published'


class ModuleForm(forms.ModelForm):
    status = forms.ChoiceField(choices=[('draft', 'Rascunho'), ('published', 'Publicado')], required=False)
    release_month = forms.IntegerField(min_value=1, required=False)

    class Meta:
        model = Module
        fields = ['title', 'status', 'release_month']

    def clean_status(self):
        return self.cleaned_data['status'] or self.instance.status or 'published'

    def clean_release_month(self):
        return self.cleaned_data['release_month'] or self.instance.release_month or 1


class EnrollmentForm(forms.Form):
    email = forms.EmailField(max_length=254, required=False)
    full_name = forms.CharField(max_length=255, required=False)
    student_id = forms.IntegerField(min_value=1, required=False)
    course_id = forms.ModelChoiceField(queryset=Course.objects.all())

    def clean(self):
        data = super().clean()
        if not data.get("student_id") and not data.get("email"):
            raise forms.ValidationError("Informe o aluno ou um e-mail válido.")
        return data


class IdentifierForm(forms.Form):
    """Validate numeric identifiers before passing them to ORM filters."""

    student_id = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    course_id = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    module_id = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    lesson_id = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    aluno = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    curso = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    aula = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    nova = forms.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
