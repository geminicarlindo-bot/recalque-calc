# calculator/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Rotas existentes
    path('', views.calculadora_view, name='calculadora'),
    path('resultado/', views.resultado_view, name='resultado'),

    # Rotas para o CRUD de Materiais
    path('catalog/materiais/', views.MaterialListView.as_view(), name='material_list'),
    path('catalog/materiais/novo/', views.MaterialCreateView.as_view(), name='material_create'),
    path('catalog/materiais/<int:pk>/editar/', views.MaterialUpdateView.as_view(), name='material_update'),
    
    # Linha Corrigida: de .as_v() para .as_view()
    path('catalog/materiais/<int:pk>/deletar/', views.MaterialDeleteView.as_view(), name='material_delete'),
    path('catalog/pecas/', views.PecaListView.as_view(), name='peca_list'),
    path('catalog/pecas/nova/', views.PecaCreateView.as_view(), name='peca_create'),
    path('catalog/pecas/<int:pk>/editar/', views.PecaUpdateView.as_view(), name='peca_update'),
    path('catalog/pecas/<int:pk>/deletar/', views.PecaDeleteView.as_view(), name='peca_delete'),
    path('catalog/tubulacoes/', views.TubulacaoListView.as_view(), name='tubulacao_list'),
    path('catalog/tubulacoes/nova/', views.TubulacaoCreateView.as_view(), name='tubulacao_create'),
    path('catalog/tubulacoes/<int:pk>/editar/', views.TubulacaoUpdateView.as_view(), name='tubulacao_update'),
    path('catalog/tubulacoes/<int:pk>/deletar/', views.TubulacaoDeleteView.as_view(), name='tubulacao_delete'),
    path('catalog/leq/', views.ComprimentoEquivalenteListView.as_view(), name='leq_list'),
    path('catalog/leq/novo/', views.ComprimentoEquivalenteCreateView.as_view(), name='leq_create'),
    path('catalog/leq/<int:pk>/editar/', views.ComprimentoEquivalenteUpdateView.as_view(), name='leq_update'),
    path('catalog/leq/<int:pk>/deletar/', views.ComprimentoEquivalenteDeleteView.as_view(), name='leq_delete'),

]