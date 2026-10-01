"""Divisao de texto em frases para caber no limite do modelo."""
import re

RE_SENTENCE_END = re.compile(r'(?<=[.!?])\s+')
RE_COMMA_BREAK = re.compile(r'(?<=,)\s+')


def _hard_split(texto: str, max_chars: int) -> list:
    """Frase maior que max_chars: quebra em virgulas, depois em espacos."""
    partes = RE_COMMA_BREAK.split(texto)
    out = []
    buf = ""
    for p in partes:
        p = p.strip()
        if not p:
            continue
        if len(p) > max_chars:
            palavras = p.split()
            cur = ""
            for w in palavras:
                if cur and len(cur) + 1 + len(w) > max_chars:
                    out.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            if cur:
                out.append(cur)
        else:
            if buf and len(buf) + 1 + len(p) > max_chars:
                out.append(buf)
                buf = ""
            buf = f"{buf} {p}".strip()
    if buf:
        out.append(buf)
    return out


def split_sentences(texto: str, max_chars: int = 250) -> list:
    """Divide em frases. Cada frase vira um bloco proprio (nao re-une)."""
    texto = texto.strip()
    if not texto:
        return []

    partes = RE_SENTENCE_END.split(texto)
    out = []
    for p in partes:
        p = p.strip()
        if not p:
            continue
        if len(p) > max_chars:
            out.extend(_hard_split(p, max_chars))
        else:
            out.append(p)
    return out
