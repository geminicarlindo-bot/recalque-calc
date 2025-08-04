# calculator/templatetags/calculator_extras.py

from django import template

# Esta linha é OBRIGATÓRIA e deve estar no nível superior do arquivo,
# não dentro de uma função ou classe.
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permite acessar o valor de um dicionário usando uma variável como chave no template.
    Uso: {{ meu_dicionario|get_item:minha_chave }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None