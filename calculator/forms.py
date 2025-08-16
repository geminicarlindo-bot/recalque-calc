# calculator/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulário de Login customizado para adicionar classes Bootstrap.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Itera sobre todos os campos do formulário
        for field_name, field in self.fields.items():
            # Adiciona a classe 'form-control' a cada campo
            field.widget.attrs.update({'class': 'form-control'})

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário de Registro customizado para adicionar classes Bootstrap.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Itera sobre todos os campos do formulário
        for field_name, field in self.fields.items():
            # Adiciona a classe 'form-control' a cada campo
            field.widget.attrs.update({'class': 'form-control'})
            # Adiciona um texto de ajuda para o campo de usuário, se quiser
            if field_name == 'username':
                field.help_text = 'Use letras, números e os caracteres @/./+/-/_.'