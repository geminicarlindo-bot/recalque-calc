# calculator/management/commands/import_leq.py

import csv
from django.core.management.base import BaseCommand
from calculator.models import Material, Peca, Tubulacao, ComprimentoEquivalente

class Command(BaseCommand):
    help = 'Importa comprimentos equivalentes de um arquivo CSV'

    def handle(self, *args, **kwargs):
        # O caminho para o nosso arquivo CSV
        csv_file_path = 'calculator/management/commands/leq_data.csv'

        self.stdout.write(self.style.SUCCESS(f'Iniciando importação de {csv_file_path}...'))

        # Limpa a tabela antiga para evitar duplicatas
        ComprimentoEquivalente.objects.all().delete()
        self.stdout.write(self.style.WARNING('Tabela de Comprimentos Equivalentes antiga foi limpa.'))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                created_count = 0
                skipped_count = 0

                for row in reader:
                    material_nome = row['material_nome']
                    peca_nome = row['peca_nome']
                    diametro_nominal = row['diametro_nominal']
                    leq_metros = float(row['leq_metros'])

                    try:
                        # Busca os objetos relacionados no banco de dados
                        material = Material.objects.get(nome__iexact=material_nome)
                        peca = Peca.objects.get(nome__iexact=peca_nome)
                        tubulacao = Tubulacao.objects.get(material=material, diametro_nominal__iexact=diametro_nominal)

                        # Cria o objeto ComprimentoEquivalente
                        ComprimentoEquivalente.objects.create(
                            peca=peca,
                            tubulacao=tubulacao,
                            comprimento_m=leq_metros
                        )
                        created_count += 1

                    except (Material.DoesNotExist, Peca.DoesNotExist, Tubulacao.DoesNotExist):
                        self.stdout.write(self.style.ERROR(
                            f"Skipping row: Não foi possível encontrar a combinação para "
                            f"Material='{material_nome}', Peça='{peca_nome}', DN='{diametro_nominal}'"
                        ))
                        skipped_count += 1
                        continue

            self.stdout.write(self.style.SUCCESS(f'Importação concluída!'))
            self.stdout.write(self.style.SUCCESS(f'{created_count} registros criados.'))
            self.stdout.write(self.style.WARNING(f'{skipped_count} registros pulados.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {csv_file_path}'))