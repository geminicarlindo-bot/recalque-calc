# recalque_core/urls.py

from django.contrib import admin
from django.urls import path, include # Certifique-se de que 'include' está aqui

urlpatterns = [
    path('admin/', admin.site.urls),
    # Este comando diz: "Qualquer URL que chegar aqui,
    # passe a responsabilidade para o arquivo 'calculator.urls'".
    path('', include('calculator.urls')),
]