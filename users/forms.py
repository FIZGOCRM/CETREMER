from django import forms
from django.core.exceptions import ValidationError
from .models import User
from django.contrib.auth.forms import PasswordResetForm


class PortalPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, portal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.portal = portal

    def get_users(self, email):
        from core.portal_routing import allows_user
        return (user for user in super().get_users(email) if allows_user(self.portal, user))

class AccountForm(forms.Form):
    email=forms.EmailField(label='E-mail')
    username=forms.CharField(required=False,max_length=150)
    avatar=forms.ImageField(required=False,label='Foto')
