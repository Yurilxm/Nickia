"""Normalizacao de texto para TTS em PT-BR."""
import re
from num2words import num2words

# Ordem importa: moeda -> porcentagem -> numero solto
RE_CURRENCY = re.compile(r'R\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{1,2}))?')
RE_PERCENT = re.compile(r'(\d+(?:[,.]\d+)?)\s*%')
RE_NUMBER = re.compile(r'\b(\d{1,3}(?:\.\d{3})+|\d+)\b')


def _valor_br(int_part: str) -> int:
    return int(int_part.replace('.', ''))


def _expand_currency(match: re.Match) -> str:
    inteiro = _valor_br(match.group(1))
    centavos = int(match.group(2)) if match.group(2) else 0

    reais = num2words(inteiro, lang='pt_BR')
    texto = f"{reais} {'real' if inteiro == 1 else 'reais'}"

    if centavos:
        c = num2words(centavos, lang='pt_BR')
        texto += f" e {c} {'centavo' if centavos == 1 else 'centavos'}"
    return texto


def _expand_percent(match: re.Match) -> str:
    valor = match.group(1).replace(',', '.')
    n = float(valor)
    if n.is_integer():
        n = int(n)
    return f"{num2words(n, lang='pt_BR')} por cento"


def _expand_number(match: re.Match) -> str:
    n = _valor_br(match.group(1))
    return num2words(n, lang='pt_BR')


def normalize(text: str) -> str:
    """Converte R$, %, e numeros soltos em palavras (PT-BR)."""
    text = RE_CURRENCY.sub(_expand_currency, text)
    text = RE_PERCENT.sub(_expand_percent, text)
    text = RE_NUMBER.sub(_expand_number, text)
    return text
