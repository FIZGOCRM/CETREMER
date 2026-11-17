from django import forms
from .models import FaqItem,SupportSubject,Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model=Ticket
        fields=['subject','title','body','device','is_private']
        labels={'subject':'Assunto','title':'Título','body':'Descreva o problema','device':'Onde aconteceu','is_private':'Chamado privado (somente eu e a equipe)'}
        widgets={'body':forms.Textarea(attrs={'rows':5})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.fields['subject'].queryset=SupportSubject.objects.filter(is_active=True)

class FaqForm(forms.ModelForm):
    class Meta:
        model=FaqItem;fields=['category','question','answer','order','is_published']
        labels={'category':'Categoria','question':'Pergunta','answer':'Resposta','order':'Ordem','is_published':'Publicada'}

class SubjectForm(forms.ModelForm):
    class Meta:
        model=SupportSubject;fields=['name','order','is_active']
        labels={'name':'Nome','order':'Ordem','is_active':'Ativo'}
