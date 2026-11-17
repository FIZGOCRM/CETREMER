from django import forms
from courses.models import Lesson
from .selectors import owned_courses

class TopicForm(forms.Form):
    course=forms.ModelChoiceField(queryset=None,required=False,label='Curso',empty_label='Geral')
    lesson=forms.ModelChoiceField(queryset=Lesson.objects.none(),required=False,label='Aula (opcional)')
    title=forms.CharField(min_length=8,max_length=200,label='Título')
    content=forms.CharField(min_length=15,widget=forms.Textarea,label='Sua dúvida')

    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['course'].queryset=owned_courses(user)
        course=self.data.get('course') if self.is_bound else self.initial.get('course')
        if str(course or '').isdigit():self.fields['lesson'].queryset=Lesson.objects.filter(module__course_id=course,status='published',module__status='published')
