# calculator/management/commands/import_tubulacoes.py

import csv
from django.core.management.base import BaseCommand
from calculator.models import Material, Tubulacao

class Command(BaseCommand):
    help = 'Importa Materiais e Tubulações de um arquivo CSV'

    def handle(self, *args, **kwargs):
        csv_file_path = 'calculator/management/commands/tubulacoes.csv'
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando importação de tubulações de {csv_file_path}...'))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                created_count = 0
                skipped_count = 0

                for row in reader:
                    # Pega (ou cria) o Material
                    material_obj, _ = Material.objects.get_or_create(
                        nome=row['material_nome'].strip(),
                        defaults={'rugosidade_mm': float(row['rugosidade_mm'])}
                    )

                    # Pega (ou cria) a Tubulação, já associando ao material
                    tubulacao_obj, created = Tubulacao.objects.get_or_create(
                        material=material_obj,
                        diametro_nominal=row['diametro_nominal'].strip(),
                        defaults={
                            'diametro_interno_mm': float(row['diametro_interno_mm']),
                            'diametro_externo_mm': float(row['diametro_externo_mm'])
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Tubulação "{tubulacao_obj.diametro_nominal}" para "{material_obj.nome}" criada.'))
                        created_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'Tubulação "{tubulacao_obj.diametro_nominal}" para "{material_obj.nome}" já existia. Pulando.'))
                        skipped_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'\nImportação de tubulações concluída!'))
            self.stdout.write(f'{created_count} novas tubulações criadas.')
            self.stdout.write(f'{skipped_count} tubulações já existentes foram puladas.')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))