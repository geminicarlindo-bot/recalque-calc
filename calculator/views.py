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
from .engine import etapa1_calcular_opcoes_diametro, etapa2_calcular_potencia_e_perdas, gerar_dados_grafico
from .models import Bomba, PontoCurvaBomba



def calculadora_view(request):
    """ETAPA 1 (GET): Exibe o formulário inicial."""
    context = {
        'materiais': Material.objects.all(),
        'stage': 'etapa1_diametro',
    }
    # Se uma submissão anterior falhou, repopulamos o formulário
    if 'dados_entrada' in request.session:
        context['dados_entrada'] = request.session.pop('dados_entrada')
    return render(request, 'calculator/calculadora.html', context)

def calcular_etapa1_view(request):
    """ETAPA 1 (POST): Recebe dados iniciais, calcula opções e exibe formulário da etapa 2."""
    if request.method != 'POST':
        return redirect('calculadora')
    
    # Salva os dados na sessão para repopular o formulário em caso de erro
    request.session['dados_entrada'] = dict(request.POST.items())

    context = {
        'materiais': Material.objects.all(),
        'pecas': Peca.objects.all(),
        'dados_entrada': request.POST,
        'stage': 'etapa2_potencia',
    }

    if request.user.is_authenticated:
        context['bombas_usuario'] = Bomba.objects.filter(user=request.user)

    try:
        consumo = float(request.POST.get('consumo_diario_litros'))
        horas = float(request.POST.get('horas_funcionamento'))
        material_id = int(request.POST.get('material'))
        
        opcoes_diametro = etapa1_calcular_opcoes_diametro(consumo, horas, material_id)
        context['opcoes_diametro'] = opcoes_diametro

    except (ValueError, TypeError, ZeroDivisionError, KeyError) as e:
        messages.error(request, f"Erro ao calcular diâmetros. Verifique os dados de entrada. (Detalhe: {e})")
        return redirect('calculadora')
        
    return render(request, 'calculator/calculadora.html', context)

def calcular_etapa2_view(request):
    """ETAPA 2 (POST): Recebe TODOS os dados, faz o cálculo final e redireciona."""
    if request.method != 'POST':
        return redirect('calculadora')

    try:
        pecas_qs = Peca.objects.all()
        pecas_suc = {p.id: int(request.POST.get(f'peca_suc_{p.id}', 0)) for p in pecas_qs if request.POST.get(f'peca_suc_{p.id}', '0').strip() not in ['', '0']}
        pecas_rec = {p.id: int(request.POST.get(f'peca_rec_{p.id}', 0)) for p in pecas_qs if request.POST.get(f'peca_rec_{p.id}', '0').strip() not in ['', '0']}
        
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
            "tubulacao_recalque_id_escolhida": int(request.POST.get('tubulacao_recalque_id_escolhida')),
            "bomba_id": int(request.POST.get('bomba_id')) if request.POST.get('bomba_id') else None,
        }
        resultados = etapa2_calcular_potencia_e_perdas(dados_completos)
        
        dados_grafico = None
        if dados_completos.get('bomba_id'):
            try:
                dados_grafico = gerar_dados_grafico(dados_completos)
            except Exception as e:
                messages.warning(request, f"Cálculo concluído, mas não foi possível gerar o gráfico: {e}")
        
        request.session['report_results'] = resultados
        request.session['report_inputs'] = dict(request.POST.lists())
        request.session['report_graph_data'] = dados_grafico
        
        nome_projeto = request.POST.get('nome_do_projeto', '').strip()
        if request.user.is_authenticated and nome_projeto:
            # Sua lógica de salvar projeto aqui
            pass
            
    except (ValueError, TypeError, ZeroDivisionError, KeyError) as e:
        messages.error(request, f"Erro no cálculo final. Verifique se todos os campos foram preenchidos. (Detalhe: {e})")
        request.session['dados_entrada'] = dict(request.POST.items())
        return redirect('calculadora')
        
    return redirect('resumo') # Redireciona para o resumo

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
    resultados = request.session.pop('report_results', None)
    dados_entrada = request.session.pop('report_inputs', None)
    dados_grafico = request.session.pop('report_graph_data', None) # <-- Pega os dados do gráfico
    context = {
        'resultados': resultados,
        'dados_entrada': dados_entrada,
        'dados_grafico': dados_grafico # <-- Passa para o template
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

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Projeto
    # Reutilizaremos o template da calculadora como um formulário pré-preenchido
    template_name = 'calculator/calculadora.html' 
    # Precisamos listar TODOS os campos que podem ser editados
    fields = [
        'nome_do_projeto', 'consumo_diario_litros', 'horas_funcionamento', 'rendimento_bomba',
        'material', 'tipo_succao', 'altura_geo_suc_m', 'comp_real_suc_m',
        'altura_geo_rec_m', 'comp_real_rec_m'
    ]
    
    def test_func(self):
        # Garante que o usuário só pode editar seus próprios projetos
        projeto = self.get_object()
        return self.request.user == projeto.user

    def get_success_url(self):
        # Para onde ir após salvar com sucesso? Para a página de detalhes do projeto.
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Projeto
    template_name = 'calculator/project_confirm_delete.html'
    success_url = reverse_lazy('project_list') # Para onde ir após deletar

    def test_func(self):
        projeto = self.get_object()
        return self.request.user == projeto.user

class BombaListView(LoginRequiredMixin, ListView):
    model = Bomba
    template_name = 'calculator/bomba_list.html'
    context_object_name = 'bombas'

    def get_queryset(self):
        # Filtra as bombas para mostrar apenas as do usuário logado
        return Bomba.objects.filter(user=self.request.user)

class BombaCreateView(LoginRequiredMixin, CreateView):
    model = Bomba
    template_name = 'calculator/bomba_form.html'
    fields = ['fabricante', 'modelo']
    success_url = reverse_lazy('bomba_list')

    def form_valid(self, form):
        # Associa a bomba recém-criada ao usuário logado
        form.instance.user = self.request.user
        messages.success(self.request, "Bomba cadastrada com sucesso!")
        return super().form_valid(form)

class BombaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Bomba
    template_name = 'calculator/bomba_form.html'
    fields = ['fabricante', 'modelo']
    success_url = reverse_lazy('bomba_list')

    def test_func(self):
        # Garante que o usuário só pode editar suas próprias bombas
        bomba = self.get_object()
        return self.request.user == bomba.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PontoCurvaFormSet = inlineformset_factory(
            Bomba, PontoCurvaBomba,
            fields=('vazao_m3h', 'altura_m'),
            extra=1, # Garante que sempre teremos pelo menos um campo extra
            can_delete=True
        )
        if self.request.POST:
            context['formset'] = PontoCurvaFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = PontoCurvaFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Bomba e sua curva de performance foram atualizadas com sucesso!")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class BombaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Bomba
    template_name = 'calculator/bomba_confirm_delete.html'
    success_url = reverse_lazy('bomba_list')
    
    def test_func(self):
        # Garante que o usuário só pode deletar suas próprias bombas
        bomba = self.get_object()
        return self.request.user == bomba.user