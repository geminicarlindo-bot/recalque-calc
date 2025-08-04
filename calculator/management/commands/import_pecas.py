# calculator/management/commands/import_pecas.py

import csv
from django.core.management.base import BaseCommand
from calculator.models import Peca

class Command(BaseCommand):
    help = 'Importa as Peças de um arquivo CSV para o banco de dados'

    def handle(self, *args, **kwargs):
        # Caminho para o arquivo CSV que acabamos de criar
        csv_file_path = 'calculator/management/commands/pecas_data.csv'
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando importação de peças de {csv_file_path}...'))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                created_count = 0
                skipped_count = 0

                for row in reader:
                    peca_nome = row['peca_nome'].strip() # .strip() remove espaços em branco extras

                    # O método get_or_create é a forma mais inteligente de fazer isso:
                    # - Se a peça já existe, ele a pega.
                    # - Se não existe, ele a cria.
                    # Isso evita duplicatas e erros se você rodar o script mais de uma vez.
                    obj, created = Peca.objects.get_or_create(
                        nome=peca_nome,
                        defaults={'descricao': f'Peça do tipo {peca_nome}'} # Adiciona uma descrição padrão
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Peça "{obj.nome}" criada com sucesso.'))
                        created_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'Peça "{obj.nome}" já existia. Pulando.'))
                        skipped_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'\nImportação de peças concluída!'))
            self.stdout.write(f'{created_count} peças novas criadas.')
            self.stdout.write(f'{skipped_count} peças já existentes foram puladas.')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))