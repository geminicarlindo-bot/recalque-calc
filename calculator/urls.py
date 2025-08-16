# calculator/urls.py (VERSÃO FINAL E CORRIGIDA)
from django.urls import path
from . import views

app_name = 'calculator'  # <== ESTA LINHA PRECISA ESTAR AQUI

urlpatterns = [
    # FLUXO PRINCIPAL DA CALCULADORA
    path('', views.calculadora_view, name='calculadora'),
    path('calcular-etapa-1/', views.calcular_etapa1_view, name='calcular_etapa1'),
    path('calcular-etapa-2/', views.calcular_etapa2_view, name='calcular_etapa2'),
    path('resumo/', views.resumo_view, name='resumo'),
    path('relatorio/', views.resultado_view, name='relatorio'),
    
    # CRUD DE PROJETOS SALVOS
    path('meus-projetos/', views.ProjectListView.as_view(), name='project_list'),
    path('projetos/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projetos/<int:pk>/editar/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projetos/<int:pk>/deletar/', views.ProjectDeleteView.as_view(), name='project_delete'),
   

    # CRUD DE CATÁLOGOS
    path('catalog/materiais/', views.MaterialListView.as_view(), name='material_list'),
    path('catalog/materiais/novo/', views.MaterialCreateView.as_view(), name='material_create'),
    path('catalog/materiais/<int:pk>/editar/', views.MaterialUpdateView.as_view(), name='material_update'),
    path('catalog/materiais/<int:pk>/deletar/', views.MaterialDeleteView.as_view(), name='material_delete'),
    
    path('catalog/pecas/', views.PecaListView.as_view(), name='peca_list'),
    path('catalog/pecas/nova/', views.PecaCreateView.as_view(), name='peca_create'),
    path('catalog/pecas/<int:pk>/editar/', views.PecaUpdateView.as_view(), name='peca_update'),
    path('catalog/pecas/<int:pk>/deletar/', views.PecaDeleteView.as_view(), name='peca_delete'),
    path('catalog/pecas/<int:pk>/editar-leqs/', views.gerenciar_leqs_por_peca, name='leq_bulk_edit'),

    path('catalog/tubulacoes/', views.TubulacaoListView.as_view(), name='tubulacao_list'),
    path('catalog/tubulacoes/nova/', views.TubulacaoCreateView.as_view(), name='tubulacao_create'),
    path('catalog/tubulacoes/<int:pk>/editar/', views.TubulacaoUpdateView.as_view(), name='tubulacao_update'),
    path('catalog/tubulacoes/<int:pk>/deletar/', views.TubulacaoDeleteView.as_view(), name='tubulacao_delete'),

    path('catalog/leq/', views.ComprimentoEquivalenteListView.as_view(), name='leq_list'),
    path('catalog/leq/novo/', views.ComprimentoEquivalenteCreateView.as_view(), name='leq_create'),
    path('catalog/leq/<int:pk>/editar/', views.ComprimentoEquivalenteUpdateView.as_view(), name='leq_update'),
    path('catalog/leq/<int:pk>/deletar/', views.ComprimentoEquivalenteDeleteView.as_view(), name='leq_delete'),

    path('bombas/', views.BombaListView.as_view(), name='bomba_list'),
    path('bombas/nova/', views.BombaCreateView.as_view(), name='bomba_create'),
    path('bombas/<int:pk>/editar/', views.BombaUpdateView.as_view(), name='bomba_update'),
    path('bombas/<int:pk>/deletar/', views.BombaDeleteView.as_view(), name='bomba_delete'),

    # path('relatorio/grafico/', views.grafico_view, name='grafico'),
  
    # Novas URLs para autenticação
    path('registro/', views.registro_view, name='registro'),
    # path('login/', views.login_view, name='login'),
    # path('logout/', views.logout_view, name='logout'),
]