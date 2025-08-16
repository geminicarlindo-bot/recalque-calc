# recalque_core/urls.py

from django.contrib import admin
from django.urls import path, include
# Importa as views de autenticação do Django
from django.contrib.auth import views as auth_views
# Importa nosso formulário de login customizado
from calculator.forms import CustomAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),

    # Nossa calculadora continua na rota principal
    path('', include('calculator.urls')),

    # Definimos a URL de login manualmente para poder passar nosso formulário
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=CustomAuthenticationForm # Aqui está a mágica!
        ),
        name='login'
    ),

    # Para as outras URLs (logout, etc.), podemos continuar usando o include padrão
    path('accounts/', include('django.contrib.auth.urls')),
]