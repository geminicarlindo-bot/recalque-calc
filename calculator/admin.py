# calculator/admin.py
from django.contrib import admin
from .models import Material, Tubulacao, Peca, ComprimentoEquivalente # Adicione Peca e ComprimentoEquivalente

# O @admin.register é uma forma elegante de registrar
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'rugosidade_mm')

@admin.register(Tubulacao)
class TubulacaoAdmin(admin.ModelAdmin):
    list_display = ('diametro_nominal', 'diametro_interno_mm', 'diametro_externo_mm', 'material')
    list_filter = ('material',)

@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')

@admin.register(ComprimentoEquivalente)
class ComprimentoEquivalenteAdmin(admin.ModelAdmin):
    list_display = ('peca', 'tubulacao', 'comprimento_m')
    list_filter = ('tubulacao__material', 'peca') # Filtro avançado!