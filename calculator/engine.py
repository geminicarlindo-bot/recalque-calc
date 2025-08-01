# calculator/engine.py

import numpy as np
from .models import Tubulacao # Importe o modelo

# ===================================================================
# CONSTANTES FÍSICAS
# Colocar constantes no início do arquivo torna o código mais legível
# e fácil de atualizar.
# ===================================================================
GRAVIDADE = 9.81  # Aceleração da gravidade (m/s²)
VISCOSIDADE_CINEMATICA_AGUA = 1.004e-6  # Viscosidade da água a 20°C (m²/s)

def calcular_sistema_recalque(
    vazao_m3h: float,
    altura_geo_total_m: float,
    comp_tubulacao_m: float,
    diametro_tub_mm: float,
    rugosidade_mm: float
) -> dict:
    """
    Calcula os parâmetros hidráulicos de um sistema de recalque simples.

    Recebe os dados de entrada e retorna um dicionário com os resultados.
    Esta função é "pura": não depende de nada do Django.
    """
    
    # --- ETAPA 1: Conversão de Unidades ---
    # É crucial garantir que todas as unidades estejam no Sistema Internacional (m, s, kg)
    # antes de iniciar os cálculos para evitar erros.
    vazao_m3s = vazao_m3h / 3600
    diametro_tub_m = diametro_tub_mm / 1000
    rugosidade_m = rugosidade_mm / 1000

    # --- ETAPA 2: Cálculos Geométricos e de Velocidade ---
    area_tub_m2 = np.pi * (diametro_tub_m / 2)**2
    velocidade_ms = vazao_m3s / area_tub_m2

    # --- ETAPA 3: Cálculo do Número de Reynolds ---
    # Reynolds nos diz se o escoamento é laminar ou turbulento.
    # É essencial para escolher a fórmula correta do fator de atrito.
    reynolds = (velocidade_ms * diametro_tub_m) / VISCOSIDADE_CINEMATICA_AGUA

    # --- ETAPA 4: Cálculo do Fator de Atrito (f) ---
    # Esta é a parte mais complexa. Usaremos a fórmula de Swamee-Jain,
    # que é uma excelente aproximação explícita para a fórmula de Colebrook-White.
    # Evita a necessidade de cálculos iterativos, sendo perfeita para nossa aplicação.
    rugosidade_relativa = rugosidade_m / diametro_tub_m
    fator_atrito_f = 0.25 / (np.log10((rugosidade_relativa / 3.7) + (5.74 / reynolds**0.9)))**2
    
    # --- ETAPA 5: Cálculo da Perda de Carga (hf) ---
    # Usamos a famosa equação Universal da Perda de Carga (Darcy-Weisbach).
    perda_carga_m = fator_atrito_f * (comp_tubulacao_m / diametro_tub_m) * (velocidade_ms**2 / (2 * GRAVIDADE))

    # --- ETAPA 6: Cálculo da Altura Manométrica Total (AMT) ---
    amt_m = altura_geo_total_m + perda_carga_m

    # --- ETAPA 7: Organizar e Retornar os Resultados ---
    # Retornar um dicionário é uma ótima prática, pois cada valor tem um nome claro.
    return {
        "altura_manometrica_total_m": amt_m,
        "perda_de_carga_m": perda_carga_m,
        "velocidade_ms": velocidade_ms,
        "numero_de_reynolds": reynolds,
        "fator_de_atrito": fator_atrito_f,
    }

# ===================================================================
# BLOCO DE TESTE
# Este código só será executado quando rodarmos o arquivo `engine.py` diretamente.
# Isso nos permite testar nossa função sem precisar ligar o servidor Django.
# ===================================================================
if __name__ == '__main__':
    print(">>> Realizando um teste do motor de cálculo...")

    # Dados de exemplo para o teste
    dados_teste = {
        "vazao_m3h": 50,
        "altura_geo_total_m": 25,
        "comp_tubulacao_m": 120,
        "diametro_tub_mm": 100,
        "rugosidade_mm": 0.15 # Ferro Fundido
    }

    # Chama a nossa função com os dados de teste
    resultados_teste = calcular_sistema_recalque(**dados_teste)

    # Imprime os resultados de forma organizada
    print("\n--- DADOS DE ENTRADA ---")
    for chave, valor in dados_teste.items():
        print(f"{chave}: {valor}")
        
    print("\n--- RESULTADOS CALCULADOS ---")
    for chave, valor in resultados_teste.items():
        # Formata os números para melhor visualização
        print(f"{chave}: {valor:.4f}")

def dimensionar_sistema_completo(
    consumo_diario_litros: float,
    horas_funcionamento: float,
    altura_geo_suc_m: float,
    altura_geo_rec_m: float,
    comp_real_suc_m: float,
    comp_real_rec_m: float,
    comp_equiv_suc_m: float,
    comp_equiv_rec_m: float,
    rendimento_bomba: float,
    material_id: int  # <-- PARÂMETRO ADICIONADO AQUI
) -> dict:
    """
    Implementa o roteiro completo de dimensionamento, com verificação
    de validade dos diâmetros encontrados.
    """
    # 1. Calcular Vazão
    dados_vazao = _calcular_vazao(consumo_diario_litros, horas_funcionamento)
    
    # 2. Dimensionar Diâmetros
    # Agora passamos o material_id para a função auxiliar
    dados_diametros = _dimensionar_diametros(
        vazao_m3s=dados_vazao['q_m3_s'],
        horas_funcionamento=horas_funcionamento,
        material_id=material_id  # <-- ARGUMENTO PASSADO AQUI
    ) 
    # --- NOVA VERIFICAÇÃO INTELIGENTE ---
    # Antes de prosseguir, verificamos se um diâmetro foi encontrado.
    if dados_diametros.get('dr_comercial_mm') is None:
        dr_calculado = dados_diametros.get('dr_calculado_mm', 0)
        raise ValueError(f"A vazão é muito alta. O diâmetro calculado ({dr_calculado:.1f} mm) excede os diâmetros comerciais disponíveis.")
        
    lt_suc = comp_real_suc_m + comp_equiv_suc_m
    lt_rec = comp_real_rec_m + comp_equiv_rec_m
    dados_hman = _calcular_h_manometrica(
        vazao_m3s=dados_vazao['q_m3_s'],
        dr_mm=dados_diametros['dr_comercial_mm'],
        ds_mm=dados_diametros['ds_comercial_mm'],
        h_geo_suc=altura_geo_suc_m,
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
        **dados_vazao,
        **dados_diametros,
        **dados_hman,
        **dados_potencia
    }
    
    return resultados_finais

def _calcular_vazao(consumo_diario_litros: float, horas_funcionamento: float) -> dict:
    """Calcula a vazão de recalque em L/h, m³/h e m³/s."""
    if horas_funcionamento == 0:
        return {} # Evita divisão por zero
        
    q_litros_h = consumo_diario_litros / horas_funcionamento
    q_m3_h = q_litros_h / 1000
    q_m3_s = q_m3_h / 3600
    
    return {
        "q_litros_h": q_litros_h,
        "q_m3_h": q_m3_h,
        "q_m3_s": q_m3_s
    }
def _dimensionar_diametros(vazao_m3s: float, horas_funcionamento: float, material_id: int) -> dict:
    """Calcula o diâmetro teórico e busca na base de dados a tubulação
    comercial correspondente para o material escolhido."""
    
    # Lista de diâmetros foi movida para o banco de dados, esta linha pode ser removida se ainda existir.
    
    # Código para calcular o diametro_recalque_calculado_mm continua o mesmo...
    X = horas_funcionamento / 24.0
    diametro_recalque_calculado_m = 1.3 * (vazao_m3s**0.5) * (X)**0.25 # Usando sua fórmula corrigida
    diametro_recalque_calculado_mm = diametro_recalque_calculado_m * 1000
    
    # Lógica de busca no banco continua a mesma...
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

    # --- MUDANÇA PRINCIPAL AQUI ---
    # Agora retornamos tanto o diâmetro interno (para os cálculos)
    # quanto o diâmetro nominal (para exibição).
    return {
        "dr_calculado_mm": diametro_recalque_calculado_mm,
        "dr_comercial_mm": tubulacao_recalque.diametro_interno_mm, # Diâmetro interno para cálculos
        "dr_nominal": tubulacao_recalque.diametro_nominal,     # Diâmetro nominal para exibição
        "ds_comercial_mm": tubulacao_succao.diametro_interno_mm, # Diâmetro interno para cálculos
        "ds_nominal": tubulacao_succao.diametro_nominal,      # Diâmetro nominal para exibição
    }

def _calcular_j_fair_whipple(vazao_m3s: float, diametro_m: float) -> float:
    """Calcula a perda de carga unitária (J) pela fórmula de Fair-Whipple-Hsiao."""
    if diametro_m == 0:
        return 0
    # J = 0.000859 * Q^1.75 / D^4.75
    return 0.000859 * (vazao_m3s**1.75) / (diametro_m**4.75)

def _calcular_h_manometrica(
    vazao_m3s: float, dr_mm: float, ds_mm: float,
    h_geo_suc: float, h_geo_rec: float,
    lt_suc: float, lt_rec: float
) -> dict:
    """Calcula as perdas de carga e a Hman total."""
    
    dr_m = dr_mm / 1000
    ds_m = ds_mm / 1000
    
    # Perda de carga unitária (J)
    j_suc = _calcular_j_fair_whipple(vazao_m3s, ds_m)
    j_rec = _calcular_j_fair_whipple(vazao_m3s, dr_m)
    
    # Perda de carga total em cada trecho (delta H)
    delta_h_suc = lt_suc * j_suc
    delta_h_rec = lt_rec * j_rec
    
    # Altura manométrica de cada trecho
    h_man_suc = h_geo_suc + delta_h_suc
    h_man_rec = h_geo_rec + delta_h_rec
    
    # Altura manométrica total
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
    
    if rendimento == 0:
        return {}
    
    vazao_l_s = vazao_m3s * 1000
    
    # P = (Q_l/s * Hman) / (75 * R)
    potencia_calculada_cv = (vazao_l_s * h_man_total) / (75 * rendimento)
    
    # Seleciona a potência comercial imediatamente superior
    potencia_comercial_cv = next((p for p in POTENCIAS_COMERCIAIS_CV if p >= potencia_calculada_cv), None)
    
    return {
        "potencia_calculada_cv": potencia_calculada_cv,
        "potencia_comercial_cv": potencia_comercial_cv
    }