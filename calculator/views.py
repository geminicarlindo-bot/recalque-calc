# calculator/views.py

from django.shortcuts import render
# Importamos a nova função e podemos remover a antiga
from .engine import dimensionar_sistema_completo
import json
from .models import Material


def calculadora_view(request):
    
    context = {}
    context['materiais'] = Material.objects.all()
    
    if request.method == 'POST':
        try:
            # Coletamos todos os dados, incluindo o material_id, e já os adicionamos ao dicionário
            dados_entrada = {
                "consumo_diario_litros": float(request.POST.get('consumo_diario_litros')),
                "horas_funcionamento": float(request.POST.get('horas_funcionamento')),
                "altura_geo_suc_m": float(request.POST.get('altura_geo_suc_m')),
                "altura_geo_rec_m": float(request.POST.get('altura_geo_rec_m')),
                "comp_real_suc_m": float(request.POST.get('comp_real_suc_m')),
                "comp_real_rec_m": float(request.POST.get('comp_real_rec_m')),
                "comp_equiv_suc_m": float(request.POST.get('comp_equiv_suc_m')),
                "comp_equiv_rec_m": float(request.POST.get('comp_equiv_rec_m')),
                "rendimento_bomba": float(request.POST.get('rendimento_bomba')),
                # Adicionamos o material_id aqui, convertendo para inteiro!
                "material_id": int(request.POST.get('material'))
            }

            # Agora, quando desempacotamos o dicionário com '**', o material_id está incluído.
            resultados = dimensionar_sistema_completo(**dados_entrada)
            
            # Colocamos tudo no contexto para enviar ao template
            context['resultados'] = resultados
            context['dados_entrada'] = dados_entrada
            # Se precisar do json para o SVG, garanta que ele seja serializável
            # context['resultados_json'] = json.dumps(resultados_serializaveis)

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['error_message'] = f"Erro nos dados de entrada. Verifique os valores e tente novamente. (Detalhe: {e})"
            # Também é bom passar os dados de volta em caso de erro para não limpar o formulário
            context['dados_entrada'] = request.POST
        
    return render(request, 'calculator/calculadora.html', context)