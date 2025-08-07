# calculator/engine.py (VERSÃO FINAL E COMPLETA)

import numpy as np
from .models import Tubulacao, ComprimentoEquivalente, Peca, Material, Bomba, PontoCurvaBomba

# --- FUNÇÕES AUXILIARES DE CÁLCULO ---
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
    dados_vazao = _calcular_vazao(consumo_diario_litros, horas_funcionamento)
    vazao_m3s = dados_vazao['q_m3_s']
    X = horas_funcionamento / 24.0
    diametro_calculado_m = 1.3 * (vazao_m3s**0.5) * (X)**0.25
    diametro_calculado_mm = diametro_calculado_m * 1000
    
    tubo_superior = Tubulacao.objects.filter(material_id=material_id, diametro_interno_mm__gte=diametro_calculado_mm).order_by('diametro_interno_mm').first()
    tubo_inferior = Tubulacao.objects.filter(material_id=material_id, diametro_interno_mm__lt=diametro_calculado_mm).order_by('-diametro_interno_mm').first()

    return {
        'calculado_mm': diametro_calculado_mm,
        'opcao_superior': _calcular_parametros_preview(vazao_m3s, tubo_superior),
        'opcao_inferior': _calcular_parametros_preview(vazao_m3s, tubo_inferior),
    }

def etapa2_calcular_potencia_e_perdas(dados_completos: dict) -> dict:
    dados_vazao = _calcular_vazao(dados_completos['consumo_diario_litros'], dados_completos['horas_funcionamento'])
    
    X = dados_completos['horas_funcionamento'] / 24.0
    diametro_calculado_m = 1.3 * (dados_vazao['q_m3_s']**0.5) * (X)**0.25
    diametro_calculado_mm = diametro_calculado_m * 1000

    tubulacao_recalque_obj = Tubulacao.objects.get(pk=dados_completos['tubulacao_recalque_id_escolhida'])
    tubulacao_succao_obj = Tubulacao.objects.filter(material_id=dados_completos['material_id'], diametro_interno_mm__gt=tubulacao_recalque_obj.diametro_interno_mm).order_by('diametro_interno_mm').first()
    if not tubulacao_succao_obj:
        tubulacao_succao_obj = tubulacao_recalque_obj
    
    altura_geo_suc_ajustada = dados_completos['altura_geo_suc_m']
    if dados_completos['tipo_succao'] == 'positiva':
        altura_geo_suc_ajustada = -abs(altura_geo_suc_ajustada)

    resultado_leq_suc = _calcular_leq_total(tubulacao_succao_obj, dados_completos['pecas_suc'])
    resultado_leq_rec = _calcular_leq_total(tubulacao_recalque_obj, dados_completos['pecas_rec'])
    
    lt_suc = dados_completos['comp_real_suc_m'] + resultado_leq_suc['total']
    lt_rec = dados_completos['comp_real_rec_m'] + resultado_leq_rec['total']

    j_suc = _calcular_j_fair_whipple(dados_vazao['q_l_s'], tubulacao_succao_obj.diametro_interno_mm)
    j_rec = _calcular_j_fair_whipple(dados_vazao['q_l_s'], tubulacao_recalque_obj.diametro_interno_mm)
    delta_h_suc = lt_suc * j_suc
    delta_h_rec = lt_rec * j_rec
    h_man_suc = altura_geo_suc_ajustada + delta_h_suc
    h_man_rec = dados_completos['altura_geo_rec_m'] + delta_h_rec
    h_man_total = h_man_suc + h_man_rec

    POTENCIAS_COMERCIAIS_CV = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0]
    potencia_calculada_cv = (dados_vazao['q_l_s'] * h_man_total) / (75 * dados_completos['rendimento_bomba'])
    potencia_comercial_cv = next((p for p in POTENCIAS_COMERCIAIS_CV if p >= potencia_calculada_cv), None)

    return {**dados_vazao, 'dr_nominal': tubulacao_recalque_obj.diametro_nominal, 'ds_nominal': tubulacao_succao_obj.diametro_nominal, 'dr_comercial_mm': tubulacao_recalque_obj.diametro_interno_mm, 'ds_comercial_mm': tubulacao_succao_obj.diametro_interno_mm, 'j_suc_m_por_m': j_suc, 'j_rec_m_por_m': j_rec, 'delta_h_suc_m': delta_h_suc, 'delta_h_rec_m': delta_h_rec, 'h_man_suc_m': h_man_suc, 'h_man_rec_m': h_man_rec, 'h_man_total_m': h_man_total, 'h_geo_suc_ajustada': altura_geo_suc_ajustada, 'potencia_calculada_cv': potencia_calculada_cv, 'potencia_comercial_cv': potencia_comercial_cv, 'comp_equiv_suc_m': resultado_leq_suc['total'], 'comp_equiv_rec_m': resultado_leq_rec['total'], 'detalhes_pecas_suc': resultado_leq_suc['detalhes'], 'detalhes_pecas_rec': resultado_leq_rec['detalhes'], 'X_factor': X,
        'dr_calculado_mm': diametro_calculado_mm,}


def _calcular_leq_total(tubulacao_obj: Tubulacao, pecas_quantidades: dict) -> dict:
    leq_total = 0.0
    detalhes_pecas = []
    if not tubulacao_obj: return {'total': 0.0, 'detalhes': []}
    for peca_id, quantidade in pecas_quantidades.items():
        try:
            comp_eq_obj = ComprimentoEquivalente.objects.select_related('peca').get(peca_id=peca_id, tubulacao=tubulacao_obj)
            leq_unitario = comp_eq_obj.comprimento_m
            leq_parcial = leq_unitario * quantidade
            leq_total += leq_parcial
            detalhes_pecas.append({'nome': comp_eq_obj.peca.nome, 'qtd': quantidade, 'leq_unitario': leq_unitario, 'leq_parcial': leq_parcial})
        except ComprimentoEquivalente.DoesNotExist: pass
    return {'total': leq_total, 'detalhes': detalhes_pecas}

def _calcular_potencia_bomba(vazao_m3s: float, h_man_total: float, rendimento: float) -> dict:
    POTENCIAS_COMERCIAIS_CV = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0]
    if rendimento == 0: return {}
    vazao_l_s = vazao_m3s * 1000
    potencia_calculada_cv = (vazao_l_s * h_man_total) / (75 * rendimento)
    potencia_comercial_cv = next((p for p in POTENCIAS_COMERCIAIS_CV if p >= potencia_calculada_cv), None)
    return {"potencia_calculada_cv": potencia_calculada_cv, "potencia_comercial_cv": potencia_comercial_cv}


# ====================================================================
# ### FUNÇÃO ESPECIALIZADA EM HMAN (ESTAVA FALTANDO) ###
# ====================================================================
def _calcular_hman_para_vazao(q_m3s: float, tubulacao_succao: Tubulacao, tubulacao_recalque: Tubulacao, dados_sistema: dict) -> dict:
    """Calcula a AMT e perdas para uma vazão e sistema específicos."""
    altura_geo_suc_ajustada = dados_sistema['altura_geo_suc_m']
    if dados_sistema['tipo_succao'] == 'positiva':
        altura_geo_suc_ajustada = -abs(altura_geo_suc_ajustada)
    
    resultado_leq_suc = _calcular_leq_total(tubulacao_succao, dados_sistema['pecas_suc'])
    resultado_leq_rec = _calcular_leq_total(tubulacao_recalque, dados_sistema['pecas_rec'])
    
    lt_suc = dados_sistema['comp_real_suc_m'] + resultado_leq_suc['total']
    lt_rec = dados_sistema['comp_real_rec_m'] + resultado_leq_rec['total']

    j_suc = _calcular_j_fair_whipple(q_m3s * 1000, tubulacao_succao.diametro_interno_mm)
    j_rec = _calcular_j_fair_whipple(q_m3s * 1000, tubulacao_recalque.diametro_interno_mm)

    delta_h_suc = lt_suc * j_suc
    delta_h_rec = lt_rec * j_rec
    
    h_man_suc = altura_geo_suc_ajustada + delta_h_suc
    h_man_rec = dados_sistema['altura_geo_rec_m'] + delta_h_rec
    h_man_total = h_man_suc + h_man_rec

    return {
        "j_suc_m_por_m": j_suc, "j_rec_m_por_m": j_rec, "delta_h_suc_m": delta_h_suc,
        "delta_h_rec_m": delta_h_rec, "h_man_suc_m": h_man_suc, "h_man_rec_m": h_man_rec,
        "h_man_total_m": h_man_total, 'comp_equiv_suc_m': resultado_leq_suc['total'],
        'comp_equiv_rec_m': resultado_leq_rec['total'], 'detalhes_pecas_suc': resultado_leq_suc['detalhes'],
        'detalhes_pecas_rec': resultado_leq_rec['detalhes'], 'h_geo_suc_ajustada': altura_geo_suc_ajustada
    }

# --- FUNÇÕES MESTRAS DE CADA ETAPA ---


def gerar_dados_grafico(dados_calculo_completo: dict) -> dict:
    """Função do Gráfico: Usa a função especializada de Hman."""
    bomba_id = dados_calculo_completo.get('bomba_id')
    if not bomba_id: return None

    bomba = Bomba.objects.get(pk=bomba_id)
    pontos_bomba = PontoCurvaBomba.objects.filter(bomba=bomba).order_by('vazao_m3h')
    
    if pontos_bomba.count() < 2: return None

    curva_bomba_data = [{'x': p.vazao_m3h, 'y': p.altura_m} for p in pontos_bomba]
    bomba_q = np.array([p['x'] for p in curva_bomba_data])
    bomba_h = np.array([p['y'] for p in curva_bomba_data])

    tubulacao_recalque = Tubulacao.objects.get(pk=dados_calculo_completo['tubulacao_recalque_id_escolhida'])
    tubulacao_succao = Tubulacao.objects.filter(material_id=dados_calculo_completo['material_id'], diametro_interno_mm__gt=tubulacao_recalque.diametro_interno_mm).order_by('diametro_interno_mm').first()
    if not tubulacao_succao: tubulacao_succao = tubulacao_recalque

    curva_sistema_data = []
    vazao_range_m3h = np.linspace(0, bomba_q.max() * 1.1, 30)
    for q_teste_m3h in vazao_range_m3h:
        q_teste_m3s = q_teste_m3h / 3600
        resultado_parcial = _calcular_hman_para_vazao(q_teste_m3s, tubulacao_succao, tubulacao_recalque, dados_calculo_completo)
        curva_sistema_data.append({'x': q_teste_m3h, 'y': resultado_parcial['h_man_total_m']})
    
    sistema_q = np.array([p['x'] for p in curva_sistema_data])
    sistema_h = np.array([p['y'] for p in curva_sistema_data])

    altura_bomba_interpolada = np.interp( sistema_q, bomba_q, bomba_h)
    idx = np.argmin(np.abs(altura_bomba_interpolada - sistema_h))
    ponto_operacao = {'x': sistema_q[idx], 'y': sistema_h[idx]}
    
    return {
        "curva_bomba": curva_bomba_data,
        "curva_sistema": curva_sistema_data,
        "ponto_operacao": ponto_operacao
    }