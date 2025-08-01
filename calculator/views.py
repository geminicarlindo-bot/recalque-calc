# calculator/views.py

from django.shortcuts import render
# Importamos a nova função e podemos remover a antiga
from .engine import dimensionar_sistema_completo
import json

def calculadora_view(request):
    
    context = {} # A "caixa" que enviaremos para o template
    
    if request.method == 'POST':
        try:
            # Coletamos todos os novos dados do formulário
            dados_entrada = {
                "consumo_diario_litros": float(request.POST.get('consumo_diario_litros')),
                "horas_funcionamento": float(request.POST.get('horas_funcionamento')),
                "altura_geo_suc_m": float(request.POST.get('altura_geo_suc_m')),
                "altura_geo_rec_m": float(request.POST.get('altura_geo_rec_m')),
                "comp_real_suc_m": float(request.POST.get('comp_real_suc_m')),
                "comp_real_rec_m": float(request.POST.get('comp_real_rec_m')),
                "comp_equiv_suc_m": float(request.POST.get('comp_equiv_suc_m')),
                "comp_equiv_rec_m": float(request.POST.get('comp_equiv_rec_m')),
                "rendimento_bomba": float(request.POST.get('rendimento_bomba'))
            }

            # Chamamos nosso novo e poderoso motor de cálculo
            resultados = dimensionar_sistema_completo(**dados_entrada)

            # Colocamos tudo no contexto para enviar ao template
            context['resultados'] = resultados
            context['dados_entrada'] = dados_entrada
            context['resultados_json'] = json.dumps(resultados) # Para o SVG

        except (ValueError, TypeError, ZeroDivisionError) as e:
            # Se o usuário digitar um valor inválido (ex: texto em vez de número)
            # ou se houver uma divisão por zero (ex: 0 horas de funcionamento),
            # nós capturamos o erro e enviamos uma mensagem amigável.
            context['error_message'] = f"Erro nos dados de entrada. Verifique os valores e tente novamente. (Detalhe: {e})"
        
    return render(request, 'calculator/calculadora.html', context)