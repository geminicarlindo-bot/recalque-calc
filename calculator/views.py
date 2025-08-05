# calculator/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Material, Peca, Tubulacao, ComprimentoEquivalente
from .engine import dimensionar_sistema_completo


def calculadora_view(request):
    """
    View unificada que exibe o formulário, processa os dados
    e mostra os resultados na mesma página.
    """
    context = {
        'materiais': Material.objects.all(),
        'pecas': Peca.objects.all()
    }

    if request.method == 'POST':
        try:
            # Coleta as quantidades de peças
            pecas_suc_quantidades = {}
            pecas_rec_quantidades = {}
            for peca in context['pecas']:
                qtd_suc = int(request.POST.get(f'peca_suc_{peca.id}', 0))
                if qtd_suc > 0:
                    pecas_suc_quantidades[peca.id] = qtd_suc
                
                qtd_rec = int(request.POST.get(f'peca_rec_{peca.id}', 0))
                if qtd_rec > 0:
                    pecas_rec_quantidades[peca.id] = qtd_rec

            # Monta o dicionário de dados para o motor de cálculo
            dados_calculo = {
                "consumo_diario_litros": float(request.POST.get('consumo_diario_litros')),
                "horas_funcionamento": float(request.POST.get('horas_funcionamento')),
                "altura_geo_suc_m": float(request.POST.get('altura_geo_suc_m')),
                "altura_geo_rec_m": float(request.POST.get('altura_geo_rec_m')),
                "comp_real_suc_m": float(request.POST.get('comp_real_suc_m')),
                "comp_real_rec_m": float(request.POST.get('comp_real_rec_m')),
                "rendimento_bomba": float(request.POST.get('rendimento_bomba')),
                "material_id": int(request.POST.get('material')),
                "tipo_succao": request.POST.get('tipo_succao', 'negativa'),
                "pecas_suc": pecas_suc_quantidades,
                "pecas_rec": pecas_rec_quantidades
            }
            
            # Executa o cálculo
            resultados = dimensionar_sistema_completo(**dados_calculo)

            # Salva os resultados e os dados de entrada no contexto
            context['resultados'] = resultados
            context['dados_entrada'] = request.POST # Para repopular o formulário
            # Preparamos uma versão "limpa" dos resultados para a SESSÃO
            resultados_para_sessao = resultados.copy()
            # Removemos as chaves que contêm objetos complexos que o JSON não entende
            resultados_para_sessao.pop('tubulacao_recalque_obj', None)
            resultados_para_sessao.pop('tubulacao_succao_obj', None)

            # Agora salvamos a VERSÃO LIMPA na sessão para a página de relatório
            request.session['report_results'] = resultados_para_sessao
            
            # request.POST já é um dicionário serializável, então está ok
            # Para garantir, convertemos para um dict padrão
            request.session['report_inputs'] = dict(request.POST.lists())

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['error_message'] = f"Erro nos dados de entrada. Verifique os valores e tente novamente. (Detalhe: {e})"
            context['dados_entrada'] = request.POST

    return render(request, 'calculator/calculadora.html', context)

# A resultado_view pode ser removida, mas vamos mantê-la por enquanto
# para a nova página de relatório.
def resultado_view(request):
    # Esta view agora será o nosso "Memorial de Cálculo"
    resultados = request.session.get('report_results', None)
    dados_entrada = request.session.get('report_inputs', None)

    # Limpamos a sessão para não mostrar o mesmo relatório antigo
    if 'report_results' in request.session:
        del request.session['report_results']
    if 'report_inputs' in request.session:
        del request.session['report_inputs']

    context = {
        'resultados': resultados,
        'dados_entrada': dados_entrada
    }
    return render(request, 'calculator/relatorio.html', context)

# ==========================================================
# ### NOVAS VIEWS PARA O CRUD DE MATERIAIS ###
# ==========================================================

class MaterialListView(ListView):
    model = Material
    template_name = 'calculator/material_list.html'  # O template que vamos criar
    context_object_name = 'materiais' # O nome da variável no template

class MaterialCreateView(CreateView):
    model = Material
    template_name = 'calculator/material_form.html' # Um template genérico para criar/editar
    fields = ['nome', 'rugosidade_mm'] # Quais campos do modelo devem aparecer no formulário
    success_url = reverse_lazy('material_list') # Para onde ir após criar com sucesso

class MaterialUpdateView(UpdateView):
    model = Material
    template_name = 'calculator/material_form.html'
    fields = ['nome', 'rugosidade_mm']
    success_url = reverse_lazy('material_list')

class MaterialDeleteView(DeleteView):
    model = Material
    template_name = 'calculator/material_confirm_delete.html' # Template de confirmação
    success_url = reverse_lazy('material_list')


class PecaListView(ListView):
    model = Peca
    template_name = 'calculator/peca_list.html'
    context_object_name = 'pecas'

class PecaCreateView(CreateView):
    model = Peca
    template_name = 'calculator/peca_form.html'
    fields = ['nome', 'descricao'] # Campos do modelo Peca
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
    # Para melhorar a performance, vamos buscar o material relacionado junto
    queryset = Tubulacao.objects.select_related('material').order_by('material__nome', 'diametro_interno_mm')

class TubulacaoCreateView(CreateView):
    model = Tubulacao
    template_name = 'calculator/tubulacao_form.html'
    # O Django automaticamente criará um campo de seleção para o ForeignKey 'material'
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
    # Otimizamos a consulta para buscar os objetos relacionados de uma vez
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

    # O inlineformset_factory cria um conjunto de formulários para ComprimentoEquivalente
    # que estão ligados a uma instância de Peca.
    LeqFormSet = inlineformset_factory(
        Peca,                      # O modelo "pai"
        ComprimentoEquivalente,    # O modelo "filho"
        fields=('tubulacao', 'comprimento_m'), # Campos a serem editados no filho
        extra=0,                   # Não mostrar formulários extras em branco
        can_delete=False           # Não permitir deletar por aqui
    )

    # Para cada tubulação que existe, garantimos que um objeto ComprimentoEquivalente
    # (mesmo que com Leq=0) exista para que o formset possa exibi-lo.
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
            return redirect('peca_list') # Volta para a lista de peças
    else:
        formset = LeqFormSet(instance=peca)

    context = {
        'formset': formset,
        'peca': peca
    }
    return render(request, 'calculator/leq_por_peca_form.html', context)