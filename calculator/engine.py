# calculator/engine.py

import numpy as np
from .models import Tubulacao, ComprimentoEquivalente # Adicione ComprimentoEquivalente

# ===================================================================
# CONSTANTES FÍSICAS
# Colocar constantes no início do arquivo torna o código mais legível
# e fácil de atualizar.
# ===================================================================
GRAVIDADE = 9.81  # Aceleração da gravidade (m/s²)
VISCOSIDADE_CINEMATICA_AGUA = 1.004e-6  # Viscosidade da água a 20°C (m²/s)

def _calcular_leq_total(tubulacao_obj: Tubulacao, pecas_quantidades: dict) -> dict:
    """Calcula o Leq total e retorna também um detalhamento por peça."""
    leq_total = 0.0
    detalhes_pecas = [] # ### NOVA LISTA PARA OS DETALHES ###
    
    if not tubulacao_obj:
        return {'total': 0.0, 'detalhes': []}
            
    for peca_id, quantidade in pecas_quantidades.items():
        try:
            comp_eq_obj = ComprimentoEquivalente.objects.select_related('peca').get(
                peca_id=peca_id,
                tubulacao=tubulacao_obj
            )
            leq_unitario = comp_eq_obj.comprimento_m
            leq_parcial = leq_unitario * quantidade
            leq_total += leq_parcial
            
            # Adicionamos os detalhes à nossa lista
            detalhes_pecas.append({
                'nome': comp_eq_obj.peca.nome,
                'qtd': quantidade,
                'leq_unitario': leq_unitario,
                'leq_parcial': leq_parcial,
            })
        except ComprimentoEquivalente.DoesNotExist:
            print(f"Aviso: Leq não encontrado para peça {peca_id} e tubulação {tubulacao_obj.id}")
            pass
            
    # ### NOVO RETORNO: UM DICIONÁRIO COMPLETO ###
    return {'total': leq_total, 'detalhes': detalhes_pecas}

def _calcular_vazao(consumo_diario_litros: float, horas_funcionamento: float) -> dict:
    """Calcula a vazão de recalque em L/h, m³/h, m³/s e L/s."""
    if horas_funcionamento == 0:
        return {}
        
    q_litros_h = consumo_diario_litros / horas_funcionamento
    q_m3_h = q_litros_h / 1000
    q_m3_s = q_m3_h / 3600
    q_l_s = q_m3_s * 1000  # ### NOVO VALOR RETORNADO ###
    
    return {
        "q_litros_h": q_litros_h,
        "q_m3_h": q_m3_h,
        "q_m3_s": q_m3_s,
        "q_l_s": q_l_s,
    }

def _dimensionar_diametros(vazao_m3s: float, horas_funcionamento: float, material_id: int) -> dict:
    """Calcula o diâmetro teórico e busca na base de dados a tubulação
    comercial correspondente para o material escolhido."""
    X = horas_funcionamento / 24.0
    diametro_recalque_calculado_m = 1.3 * (vazao_m3s**0.5) * (X)**0.25
    diametro_recalque_calculado_mm = diametro_recalque_calculado_m * 1000

    tubulacao_recalque = Tubulacao.objects.filter(
        material_id=material_id,
        diametro_interno_mm__gte=diametro_recalque_calculado_mm
    ).order_by('diametro_interno_mm').first()

    if not tubulacao_recalque:
        raise ValueError(f"Não foi encontrada tubulação comercial para o diâmetro calculado de {diametro_recalque_calculado_mm:.2f}mm no material selecionado.")

    tubulacao_succao = Tubulacao.objects.filter(
        material_id=material_id,
        diametro_interno_mm__gt=tubulacao_recalque.diametro_interno_mm
    ).order_by('diametro_interno_mm').first()
    if not tubulacao_succao:
        tubulacao_succao = tubulacao_recalque
    
    # ### CORREÇÃO 3: Adicionamos de volta os objetos da tubulação no retorno ###
    # Eles são necessários para a função _calcular_leq_total
    return {
        "dr_calculado_mm": diametro_recalque_calculado_mm,
        "dr_comercial_mm": tubulacao_recalque.diametro_interno_mm,
        "dr_nominal": tubulacao_recalque.diametro_nominal,
        "ds_comercial_mm": tubulacao_succao.diametro_interno_mm,
        "ds_nominal": tubulacao_succao.diametro_nominal,
        "tubulacao_recalque_obj": tubulacao_recalque, # Objeto necessário
        "tubulacao_succao_obj": tubulacao_succao,   # Objeto necessário
        "X_factor": X,  # <-- ADICIONAMOS ESTA LINHA

    }


def _calcular_j_fair_whipple(vazao_l_s: float, diametro_mm: float) -> float:
    """Calcula a perda de carga unitária (J) pela fórmula de Fair-Whipple-Hsiao,
    utilizando vazão em L/s e diâmetro em mm."""
    
    if diametro_mm == 0:
        return 0
        
 
    return 869000 * (vazao_l_s**1.75) / (diametro_mm**4.75)

def _calcular_h_manometrica(
    vazao_m3s: float, dr_mm: float, ds_mm: float,
    h_geo_suc: float, h_geo_rec: float,
    lt_suc: float, lt_rec: float
) -> dict:
    """Calcula as perdas de carga e a Hman total."""
    
    # --- MUDANÇA AQUI ---
    # Convertemos a vazão para L/s ANTES de chamar a função de cálculo de J.
    vazao_l_s = vazao_m3s * 1000
    
    # Não precisamos mais converter os diâmetros de mm para m aqui.
    # dr_m = dr_mm / 1000 <--- REMOVIDO
    # ds_m = ds_mm / 1000 <--- REMOVIDO
    
    # Perda de carga unitária (J)
    # Agora passamos os valores diretamente em L/s e mm.
    j_suc = _calcular_j_fair_whipple(vazao_l_s, ds_mm)
    j_rec = _calcular_j_fair_whipple(vazao_l_s, dr_mm)
    
    # O resto da função continua exatamente igual.
    delta_h_suc = lt_suc * j_suc
    delta_h_rec = lt_rec * j_rec
    
    h_man_suc = h_geo_suc + delta_h_suc
    h_man_rec = h_geo_rec + delta_h_rec
    
    h_man_total = h_man_suc + h_man_rec
    
    return {
        "j_suc_m_por_m": j_suc,
        "j_rec_m_por_m": j_rec,
        "delta_h_suc_m": delta_h_suc,
        "delta_h_rec_m": delta_h_rec,
        "h_man_suc_m": h_man_suc,
        "h_man_rec_m": h_man_rec,
        "h_man_total_m": h_man_total
    }

def _calcular_potencia_bomba(vazao_m3s: float, h_man_total: float, rendimento: float) -> dict:
    """Calcula a potência da bomba em CV e seleciona a potência comercial."""
    POTENCIAS_COMERCIAIS_CV = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0]
    if rendimento == 0: return {}
    vazao_l_s = vazao_m3s * 1000
    potencia_calculada_cv = (vazao_l_s * h_man_total) / (75 * rendimento)
    potencia_comercial_cv = next((p for p in POTENCIAS_COMERCIAIS_CV if p >= potencia_calculada_cv), None)
    return {
        "potencia_calculada_cv": potencia_calculada_cv,
        "potencia_comercial_cv": potencia_comercial_cv
    }


def dimensionar_sistema_completo(
    consumo_diario_litros: float, horas_funcionamento: float,
    altura_geo_suc_m: float, altura_geo_rec_m: float,
    comp_real_suc_m: float, comp_real_rec_m: float,
    rendimento_bomba: float, material_id: int,
    # ==========================================================
    # CORREÇÃO: Adicionados os parâmetros que faltavam aqui
    pecas_suc: dict, 
    pecas_rec: dict,
    tipo_succao: str

) -> dict:
    """
    Implementa o roteiro completo de dimensionamento.
    """
    dados_vazao = _calcular_vazao(consumo_diario_litros, horas_funcionamento)
    
    dados_diametros = _dimensionar_diametros(
        vazao_m3s=dados_vazao['q_m3_s'],
        horas_funcionamento=horas_funcionamento,
        material_id=material_id
    )
    
    altura_geo_suc_ajustada = altura_geo_suc_m
    if tipo_succao == 'positiva':
        # Se a sucção for positiva (aspirante), o desnível é negativo no cálculo da energia
        altura_geo_suc_ajustada = -abs(altura_geo_suc_m)

    if dados_diametros.get('dr_comercial_mm') is None:
        dr_calculado = dados_diametros.get('dr_calculado_mm', 0)
        raise ValueError(f"A vazão é muito alta. O diâmetro calculado ({dr_calculado:.1f} mm) excede os diâmetros comerciais disponíveis.")
    
    tubulacao_recalque_obj = dados_diametros['tubulacao_recalque_obj']
    tubulacao_succao_obj = dados_diametros['tubulacao_succao_obj']

    # Agora recebemos o dicionário completo
    resultado_leq_suc = _calcular_leq_total(tubulacao_succao_obj, pecas_suc)
    resultado_leq_rec = _calcular_leq_total(tubulacao_recalque_obj, pecas_rec)
    
    # Usamos o total para os cálculos
    comp_equiv_suc_m = resultado_leq_suc['total']
    comp_equiv_rec_m = resultado_leq_rec['total']

    lt_suc = comp_real_suc_m + comp_equiv_suc_m
    lt_rec = comp_real_rec_m + comp_equiv_rec_m
    
    dados_hman = _calcular_h_manometrica(
        vazao_m3s=dados_vazao['q_m3_s'],
        dr_mm=dados_diametros['dr_comercial_mm'],
        ds_mm=dados_diametros['ds_comercial_mm'],
        h_geo_suc=altura_geo_suc_ajustada,
        h_geo_rec=altura_geo_rec_m,
        lt_suc=lt_suc,
        lt_rec=lt_rec
    )
    
    dados_potencia = _calcular_potencia_bomba(
        vazao_m3s=dados_vazao['q_m3_s'],
        h_man_total=dados_hman['h_man_total_m'],
        rendimento=rendimento_bomba
    )
    
    resultados_finais = {
        **dados_vazao, **dados_diametros, **dados_hman, **dados_potencia,
        "comp_equiv_suc_m": comp_equiv_suc_m,
        "comp_equiv_rec_m": comp_equiv_rec_m,
        # ### NOVOS DADOS PARA O RELATÓRIO ###
        "detalhes_pecas_suc": resultado_leq_suc['detalhes'],
        "detalhes_pecas_rec": resultado_leq_rec['detalhes'],
        "h_geo_suc_ajustada": altura_geo_suc_ajustada,
    }
    
    return resultados_finais