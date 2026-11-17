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


class CourseForm(forms.ModelForm):
    price = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )

    class Meta:
        model = Course
        fields = [
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

    def clean_live_calendar_url(self):
        url = self.cleaned_data["live_calendar_url"]
        if url and urlparse(url).hostname != "calendar.google.com":
            raise forms.ValidationError("Use o link público de uma agenda do Google.")
        return url


class LessonForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = Lesson
        fields = ["module", "title", "description", "video_url"]

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
