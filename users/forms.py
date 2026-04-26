from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'institution_name', 'role')
        labels = {
            'username': 'Nume utilizator',
            'email': 'Adresă email',
            'institution_name': 'Instituție',
            'role': 'Rol în instituție',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Parolă'
        self.fields['password2'].label = 'Confirmare parolă'
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})