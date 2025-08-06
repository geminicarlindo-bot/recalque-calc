# calculator/engine.py (VERSÃO FINAL E CORRIGIDA)

import numpy as np
from .models import Tubulacao, ComprimentoEquivalente, Peca, Material

GRAVIDADE = 9.81
VISCOSIDADE_CINEMATICA_AGUA = 1.004e-6

def _calcular_vazao(consumo_diario_litros: float, horas_funcionamento: float) -> dict:
    if horas_funcionamento <= 0:
        raise ValueError("Horas de funcionamento deve ser um valor positivo.")
    q_litros_h = consumo_diario_litros / horas_funcionamento
    q_m3_h = q_litros_h / 1000
    q_m3_s = q_m3_h / 3600
    q_l_s = q_m3_s * 1000
    return {"q_litros_h": q_litros_h, "q_m3_h": q_m3_h, "q_m3_s": q_m3_s, "q_l_s": q_l_s}

def _calcular_j_fair_whipple(vazao_l_s: float, diametro_mm: float) -> float:
    if diametro_mm == 0: return 0.0
    return 869000 * (vazao_l_s**1.75) / (diametro_mm**4.75)

def _calcular_parametros_preview(vazao_m3s: float, tubulacao: Tubulacao) -> dict:
    if not tubulacao:
        return {'velocidade_ms': 0, 'j_m_por_m': 0, 'tubulacao_obj': None}
    diametro_interno_m = tubulacao.diametro_interno_mm / 1000
    area_tub_m2 = np.pi * (diametro_interno_m / 2)**2
    velocidade_ms = vazao_m3s / area_tub_m2
    j_m_por_m = _calcular_j_fair_whipple(vazao_m3s * 1000, tubulacao.diametro_interno_mm)
    return {'velocidade_ms': velocidade_ms, 'j_m_por_m': j_m_por_m, 'tubulacao_obj': tubulacao}

def etapa1_calcular_opcoes_diametro(consumo_diario_litros: float, horas_funcionamento: float, material_id: int) -> dict:
    """Função da Etapa 1: Calcula a vazão e as opções de diâmetro."""
    dados_vazao = _calcular_vazao(consumo_diario_litros, horas_funcionamento)
    vazao_m3s = dados_vazao['q_m3_s']
    X = horas_funcionamento / 24.0
    diametro_calculado_m = 1.3 * (vazao_m3s**0.5) * (X)**0.25
    diametro_calculado_mm = diametro_calculado_m * 1000
    
    tubo_superior = Tubulacao.objects.filter(material_id=material_id, diametro_interno_mm__gte=diametro_calculado_mm).order_by('diametro_interno_mm').first()
    tubo_inferior = Tubulacao.objects.filter(material_id=material_id, diametro_interno_mm__lt=diametro_calculado_mm).order_by('-diametro_interno_mm').first()

    return {
        'dados_vazao': dados_vazao,
        'calculado_mm': diametro_calculado_mm,
        'opcao_superior': _calcular_parametros_preview(vazao_m3s, tubo_superior),
        'opcao_inferior': _calcular_parametros_preview(vazao_m3s, tubo_inferior),
    }

def etapa2_calcular_potencia_e_perdas(dados_completos: dict) -> dict:
    """Função da Etapa 2: Recebe todos os dados e retorna o resultado final."""
    dados_vazao = _calcular_vazao(dados_completos['consumo_diario_litros'], dados_completos['horas_funcionamento'])
    
    tubulacao_recalque_obj = Tubulacao.objects.get(pk=dados_completos['tubulacao_recalque_id_escolhida'])
    tubulacao_succao_obj = Tubulacao.objects.filter(material_id=dados_completos['material_id'], diametro_interno_mm__gt=tubulacao_recalque_obj.diametro_interno_mm).order_by('diametro_interno_mm').first()
    if not tubulacao_succao_obj:
        tubulacao_succao_obj = tubulacao_recalque_obj
    
    # Leq
    leq_total_suc = 0.0
    detalhes_pecas_suc = []
    for peca_id, qtd in dados_completos['pecas_suc'].items():
        try:
            comp_eq = ComprimentoEquivalente.objects.select_related('peca').get(peca_id=peca_id, tubulacao=tubulacao_succao_obj)
            leq_parcial = comp_eq.comprimento_m * qtd
            leq_total_suc += leq_parcial
            detalhes_pecas_suc.append({'nome': comp_eq.peca.nome, 'qtd': qtd, 'leq_unitario': comp_eq.comprimento_m, 'leq_parcial': leq_parcial})
        except ComprimentoEquivalente.DoesNotExist: pass

    leq_total_rec = 0.0
    detalhes_pecas_rec = []
    for peca_id, qtd in dados_completos['pecas_rec'].items():
        try:
            comp_eq = ComprimentoEquivalente.objects.select_related('peca').get(peca_id=peca_id, tubulacao=tubulacao_recalque_obj)
            leq_parcial = comp_eq.comprimento_m * qtd
            leq_total_rec += leq_parcial
            detalhes_pecas_rec.append({'nome': comp_eq.peca.nome, 'qtd': qtd, 'leq_unitario': comp_eq.comprimento_m, 'leq_parcial': leq_parcial})
        except ComprimentoEquivalente.DoesNotExist: pass

    # Hman
    altura_geo_suc_ajustada = dados_completos['altura_geo_suc_m']
    if dados_completos['tipo_succao'] == 'positiva':
        altura_geo_suc_ajustada = -abs(altura_geo_suc_ajustada)
    
    lt_suc = dados_completos['comp_real_suc_m'] + leq_total_suc
    lt_rec = dados_completos['comp_real_rec_m'] + leq_total_rec

    j_suc = _calcular_j_fair_whipple(dados_vazao['q_l_s'], tubulacao_succao_obj.diametro_interno_mm)
    j_rec = _calcular_j_fair_whipple(dados_vazao['q_l_s'], tubulacao_recalque_obj.diametro_interno_mm)

    delta_h_suc = lt_suc * j_suc
    delta_h_rec = lt_rec * j_rec
    
    h_man_suc = altura_geo_suc_ajustada + delta_h_suc
    h_man_rec = dados_completos['altura_geo_rec_m'] + delta_h_rec
    h_man_total = h_man_suc + h_man_rec

    # Potência
    POTENCIAS_COMERCIAIS_CV = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0]
    potencia_calculada_cv = (dados_vazao['q_l_s'] * h_man_total) / (75 * dados_completos['rendimento_bomba'])
    potencia_comercial_cv = next((p for p in POTENCIAS_COMERCIAIS_CV if p >= potencia_calculada_cv), None)

    return {
        'q_m3_h': dados_vazao['q_m3_h'], 'q_l_s': dados_vazao['q_l_s'], 'q_m3_s': dados_vazao['q_m3_s'],
        'dr_nominal': tubulacao_recalque_obj.diametro_nominal, 'ds_nominal': tubulacao_succao_obj.diametro_nominal,
        'dr_comercial_mm': tubulacao_recalque_obj.diametro_interno_mm, 'ds_comercial_mm': tubulacao_succao_obj.diametro_interno_mm,
        'j_suc_m_por_m': j_suc, 'j_rec_m_por_m': j_rec,
        'delta_h_suc_m': delta_h_suc, 'delta_h_rec_m': delta_h_rec,
        'h_man_suc_m': h_man_suc, 'h_man_rec_m': h_man_rec,
        'h_man_total_m': h_man_total, 'h_geo_suc_ajustada': altura_geo_suc_ajustada,
        'potencia_calculada_cv': potencia_calculada_cv, 'potencia_comercial_cv': potencia_comercial_cv,
        'comp_equiv_suc_m': leq_total_suc, 'comp_equiv_rec_m': leq_total_rec,
        'detalhes_pecas_suc': detalhes_pecas_suc, 'detalhes_pecas_rec': detalhes_pecas_rec,
    }