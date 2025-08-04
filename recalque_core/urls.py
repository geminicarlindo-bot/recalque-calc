# recalque_core/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Adicionamos esta linha:
    # Ela cria automaticamente as rotas como /login/, /logout/, etc.
    path('accounts/', include('django.contrib.auth.urls')),

    # Nossa calculadora continua na rota principal
    path('', include('calculator.urls')),
]