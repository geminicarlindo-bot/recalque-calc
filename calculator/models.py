# calculator/models.py
from django.db import models

class Material(models.Model):
    nome = models.CharField(max_length=100, unique=True, help_text="Ex: PVC Soldável, Aço Carbono")
    rugosidade_mm = models.FloatField(help_text="Rugosidade absoluta (ε) em milímetros")

    def __str__(self):
        return self.nome

class Tubulacao(models.Model):
    # O ForeignKey cria a relação: Cada tubulação PERTENCE a um material.
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='tubulacoes')
    
    diametro_nominal = models.CharField(max_length=20, help_text="Representação comercial. Ex: '50mm' ou '2 polegadas'")
    diametro_interno_mm = models.FloatField(help_text="Diâmetro interno real em milímetros (usado nos cálculos)")
    diametro_externo_mm = models.FloatField(help_text="Diâmetro externo real em milímetros")

    class Meta:
        # Garante que não teremos o mesmo diâmetro interno para o mesmo material duas vezes
        unique_together = ('material', 'diametro_interno_mm')
        ordering = ['material', 'diametro_interno_mm'] # Ordena os tubos por tamanho

    def __str__(self):
        return f"{self.material.nome} - DN {self.diametro_nominal} ({self.diametro_interno_mm}mm interno)"