from django import forms
from django.core.exceptions import ValidationError
from .models import User

class AccountForm(forms.Form):
    email=forms.EmailField(label='E-mail')
    username=forms.CharField(required=False,max_length=150)
    avatar=forms.ImageField(required=False,label='Foto')
