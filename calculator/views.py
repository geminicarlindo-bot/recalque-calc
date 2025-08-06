# calculator/views.py (VERSÃO CORRIGIDA)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.http import HttpResponse
from .engine import etapa1_calcular_opcoes_diametro, etapa2_calcular_potencia_e_perdas

from .models import Material, Peca, Tubulacao, ComprimentoEquivalente, Projeto
from .engine import etapa1_calcular_opcoes_diametro, etapa2_calcular_potencia_e_perdas

def calculadora_view(request):
    """ETAPA 1 (GET): Exibe o formulário inicial para cálculo do diâmetro."""
    context = {
        'materiais': Material.objects.all(),
        'stage': 'etapa1_diametro', # Sinaliza ao template qual formulário mostrar
    }
    # Se uma submissão anterior falhou, repopulamos o formulário
    if 'dados_entrada' in request.session:
        context['dados_entrada'] = request.session.pop('dados_entrada')
        
    return render(request, 'calculator/calculadora.html', context)

def calcular_etapa1_view(request):
    """ETAPA 1 (POST): Recebe dados iniciais, calcula opções de diâmetro e exibe o formulário da etapa 2."""
    if request.method != 'POST':
        return redirect('calculadora')

    context = {
        'materiais': Material.objects.all(),
        'pecas': Peca.objects.all(),
        'dados_entrada': request.POST, # Passa os dados de volta para repopular
        'stage': 'etapa2_potencia', # Sinaliza para mostrar a segunda parte do formulário
    }
    
    try:
        consumo = float(request.POST.get('consumo_diario_litros'))
        horas = float(request.POST.get('horas_funcionamento'))
        material_id = int(request.POST.get('material'))
        
        opcoes_diametro = etapa1_calcular_opcoes_diametro(consumo, horas, material_id)
        context['opcoes_diametro'] = opcoes_diametro

    except (ValueError, TypeError, ZeroDivisionError, KeyError) as e:
        messages.error(request, f"Erro ao calcular diâmetros. Verifique os dados de entrada. (Detalhe: {e})")
        request.session['dados_entrada'] = request.POST # Salva os dados para repopular o form
        return redirect('calculadora')
        
    return render(request, 'calculator/calculadora.html', context)

def calcular_etapa2_view(request):
    """ETAPA 2 (POST): Recebe todos os dados, faz o cálculo final e redireciona para o relatório."""
    if request.method != 'POST':
        return redirect('calculadora')

    try:
        pecas_qs = Peca.objects.all()
        pecas_suc = {p.id: int(request.POST.get(f'peca_suc_{p.id}', 0)) for p in pecas_qs if request.POST.get(f'peca_suc_{p.id}')}
        pecas_rec = {p.id: int(request.POST.get(f'peca_rec_{p.id}', 0)) for p in pecas_qs if request.POST.get(f'peca_rec_{p.id}')}
        
        dados_completos = {
            "consumo_diario_litros": float(request.POST.get('consumo_diario_litros')),
            "horas_funcionamento": float(request.POST.get('horas_funcionamento')),
            "altura_geo_suc_m": float(request.POST.get('altura_geo_suc_m')),
            "altura_geo_rec_m": float(request.POST.get('altura_geo_rec_m')),
            "comp_real_suc_m": float(request.POST.get('comp_real_suc_m')),
            "comp_real_rec_m": float(request.POST.get('comp_real_rec_m')),
            "rendimento_bomba": float(request.POST.get('rendimento_bomba')),
            "material_id": int(request.POST.get('material')),
            "tipo_succao": request.POST.get('tipo_succao', 'negativa'),
            "pecas_suc": pecas_suc, "pecas_rec": pecas_rec,
            "tubulacao_recalque_id_escolhida": int(request.POST.get('tubulacao_recalque_id_escolhida'))
        }
        resultados = etapa2_calcular_potencia_e_perdas(dados_completos)
        
        request.session['report_results'] = resultados
        request.session['report_inputs'] = dict(request.POST.lists())
        
        nome_projeto = request.POST.get('nome_do_projeto', '').strip()
        if request.user.is_authenticated and nome_projeto:
            # Sua lógica para salvar o projeto aqui
            pass
            
    except (ValueError, TypeError, ZeroDivisionError, KeyError) as e:
        messages.error(request, f"Erro no cálculo final. Verifique se todos os campos foram preenchidos. (Detalhe: {e})")
        request.session['dados_entrada'] = request.POST
        return redirect('calculadora')
        
    return redirect('resumo')

def resumo_view(request):
    """
    Página intermediária que exibe os resultados principais.
    Ela lê os dados da sessão, mas não os apaga.
    """
    # .get() apenas lê o dado da sessão. .pop() (usado na view do relatório) lê e apaga.
    resultados = request.session.get('report_results', None)

    # Se não houver resultados na sessão, redireciona para a calculadora
    if not resultados:
        messages.warning(request, "Não há resultados para exibir. Por favor, faça um cálculo primeiro.")
        return redirect('calculadora')

    context = {
        'resultados': resultados
    }
    return render(request, 'calculator/resumo.html', context)

def resultado_view(request):
    # Esta view continua igual
    resultados = request.session.pop('report_results', None)
    dados_entrada = request.session.pop('report_inputs', None)
    context = {'resultados': resultados, 'dados_entrada': dados_entrada}
    return render(request, 'calculator/relatorio.html', context)

def resultado_view(request):
    """Exibe o relatório final com os resultados."""
    resultados = request.session.get('report_results', None)
    dados_entrada = request.session.get('report_inputs', None)
    
    if not resultados:
        messages.warning(request, "Não há resultados para exibir. Faça um cálculo primeiro.")
        return redirect('calculadora')
    
    context = {
        'resultados': resultados, 
        'dados_entrada': dados_entrada
    }
    return render(request, 'calculator/relatorio.html', context)

# [RESTO DAS VIEWS PERMANECE IGUAL...]
class MaterialListView(LoginRequiredMixin, ListView):
    model = Material
    template_name = 'calculator/material_list.html'
    context_object_name = 'materiais'

class MaterialCreateView(LoginRequiredMixin, CreateView):
    model = Material
    template_name = 'calculator/material_form.html'
    fields = ['nome', 'rugosidade_mm']
    success_url = reverse_lazy('material_list')

class MaterialUpdateView(LoginRequiredMixin, UpdateView):
    model = Material
    template_name = 'calculator/material_form.html'
    fields = ['nome', 'rugosidade_mm']
    success_url = reverse_lazy('material_list')

class MaterialDeleteView(LoginRequiredMixin, DeleteView):
    model = Material
    template_name = 'calculator/material_confirm_delete.html'
    success_url = reverse_lazy('material_list')

class PecaListView(ListView):
    model = Peca
    template_name = 'calculator/peca_list.html'
    context_object_name = 'pecas'

class PecaCreateView(CreateView):
    model = Peca
    template_name = 'calculator/peca_form.html'
    fields = ['nome', 'descricao']
    success_url = reverse_lazy('peca_list')

class PecaUpdateView(UpdateView):
    model = Peca
    template_name = 'calculator/peca_form.html'
    fields = ['nome', 'descricao']
    success_url = reverse_lazy('peca_list')

class PecaDeleteView(DeleteView):
    model = Peca
    template_name = 'calculator/peca_confirm_delete.html'
    success_url = reverse_lazy('peca_list')

class TubulacaoListView(ListView):
    model = Tubulacao
    template_name = 'calculator/tubulacao_list.html'
    context_object_name = 'tubulacoes'
    queryset = Tubulacao.objects.select_related('material').order_by('material__nome', 'diametro_interno_mm')

class TubulacaoCreateView(CreateView):
    model = Tubulacao
    template_name = 'calculator/tubulacao_form.html'
    fields = ['material', 'diametro_nominal', 'diametro_interno_mm', 'diametro_externo_mm']
    success_url = reverse_lazy('tubulacao_list')

class TubulacaoUpdateView(UpdateView):
    model = Tubulacao
    template_name = 'calculator/tubulacao_form.html'
    fields = ['material', 'diametro_nominal', 'diametro_interno_mm', 'diametro_externo_mm']
    success_url = reverse_lazy('tubulacao_list')

class TubulacaoDeleteView(DeleteView):
    model = Tubulacao
    template_name = 'calculator/tubulacao_confirm_delete.html'
    success_url = reverse_lazy('tubulacao_list')

class ComprimentoEquivalenteListView(ListView):
    model = ComprimentoEquivalente
    template_name = 'calculator/leq_list.html'
    context_object_name = 'comprimentos_equivalentes'
    queryset = ComprimentoEquivalente.objects.select_related('peca', 'tubulacao__material').order_by('peca__nome', 'tubulacao__diametro_interno_mm')

class ComprimentoEquivalenteCreateView(CreateView):
    model = ComprimentoEquivalente
    template_name = 'calculator/leq_form.html'
    fields = ['peca', 'tubulacao', 'comprimento_m']
    success_url = reverse_lazy('leq_list')

class ComprimentoEquivalenteUpdateView(UpdateView):
    model = ComprimentoEquivalente
    template_name = 'calculator/leq_form.html'
    fields = ['peca', 'tubulacao', 'comprimento_m']
    success_url = reverse_lazy('leq_list')

class ComprimentoEquivalenteDeleteView(DeleteView):
    model = ComprimentoEquivalente
    template_name = 'calculator/leq_confirm_delete.html'
    success_url = reverse_lazy('leq_list')

def gerenciar_leqs_por_peca(request, pk):
    peca = get_object_or_404(Peca, pk=pk)

    LeqFormSet = inlineformset_factory(
        Peca,
        ComprimentoEquivalente,
        fields=('tubulacao', 'comprimento_m'),
        extra=0,
        can_delete=False
    )

    for tubulacao in Tubulacao.objects.all():
        ComprimentoEquivalente.objects.get_or_create(
            peca=peca,
            tubulacao=tubulacao,
            defaults={'comprimento_m': 0.0}
        )

    if request.method == 'POST':
        formset = LeqFormSet(request.POST, instance=peca)
        if formset.is_valid():
            formset.save()
            return redirect('peca_list')
    else:
        formset = LeqFormSet(instance=peca)

    context = {
        'formset': formset,
        'peca': peca
    }
    return render(request, 'calculator/leq_por_peca_form.html', context)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Projeto
    template_name = 'calculator/project_list.html'
    context_object_name = 'projetos'

    def get_queryset(self):
        return Projeto.objects.filter(user=self.request.user).order_by('-data_criacao')

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Projeto
    template_name = 'calculator/project_detail.html'
    context_object_name = 'projeto'

    def test_func(self):
        projeto = self.get_object()
        return self.request.user == projeto.user