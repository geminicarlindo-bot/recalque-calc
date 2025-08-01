# calculator/views.py

from django.shortcuts import render
# Importamos a nova função e podemos remover a antiga
from .engine import dimensionar_sistema_completo
import json
from .models import Material, Peca

def calculadora_view(request):
    
    context = {}
    context['materiais'] = Material.objects.all()
    context['pecas'] = Peca.objects.all() # Garanta que as peças estão sendo enviadas para o template
    
    if request.method == 'POST':
        try:
            # ==========================================================
            # ### CORREÇÃO PRINCIPAL COMEÇA AQUI ###
            # ==========================================================

            # 1. Coletamos as quantidades de peças do formulário
            pecas_suc_quantidades = {}
            pecas_rec_quantidades = {}
            for peca in Peca.objects.all():
                # Para a sucção, pegamos o valor do input com nome 'peca_suc_ID_DA_PECA'
                qtd_suc = int(request.POST.get(f'peca_suc_{peca.id}', 0))
                if qtd_suc > 0:
                    pecas_suc_quantidades[peca.id] = qtd_suc
                
                # Para o recalque, pegamos o valor do input com nome 'peca_rec_ID_DA_PECA'
                qtd_rec = int(request.POST.get(f'peca_rec_{peca.id}', 0))
                if qtd_rec > 0:
                    pecas_rec_quantidades[peca.id] = qtd_rec

            # 2. Montamos o dicionário de entrada para o motor
            dados_entrada = {
                "consumo_diario_litros": float(request.POST.get('consumo_diario_litros')),
                "horas_funcionamento": float(request.POST.get('horas_funcionamento')),
                "altura_geo_suc_m": float(request.POST.get('altura_geo_suc_m')),
                "altura_geo_rec_m": float(request.POST.get('altura_geo_rec_m')),
                "comp_real_suc_m": float(request.POST.get('comp_real_suc_m')),
                "comp_real_rec_m": float(request.POST.get('comp_real_rec_m')),
                "rendimento_bomba": float(request.POST.get('rendimento_bomba')),
                "material_id": int(request.POST.get('material')),
                "pecas_suc": pecas_suc_quantidades,  # O dicionário de peças da sucção
                "pecas_rec": pecas_rec_quantidades   # O dicionário de peças do recalque
            }
            # ==========================================================
            # ### CORREÇÃO PRINCIPAL TERMINA AQUI ###
            # ==========================================================

            # 3. Chamamos o motor com todos os dados corretos
            resultados = dimensionar_sistema_completo(**dados_entrada)
            
            context['resultados'] = resultados
            context['dados_entrada'] = dados_entrada

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['error_message'] = f"Erro nos dados de entrada. Verifique os valores e tente novamente. (Detalhe: {e})"
            context['dados_entrada'] = request.POST
        
    return render(request, 'calculator/calculadora.html', context)