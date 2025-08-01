# calculator/urls.py

from django.urls import path
from . import views # Importa o arquivo views.py da mesma pasta

urlpatterns = [
    # Quando o usuário acessar a URL raiz do nosso app,
    # a função 'calculadora_view' do nosso arquivo 'views.py' será chamada.
    # O 'name' é um apelido útil que usaremos mais tarde.
    path('', views.calculadora_view, name='calculadora'),
]