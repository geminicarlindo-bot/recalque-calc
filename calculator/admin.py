# calculator/admin.py
from django.contrib import admin
from .models import Material, Tubulacao

# O @admin.register é uma forma elegante de registrar
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'rugosidade_mm')

@admin.register(Tubulacao)
class TubulacaoAdmin(admin.ModelAdmin):
    list_display = ('diametro_nominal', 'diametro_interno_mm', 'diametro_externo_mm', 'material')
    list_filter = ('material',)