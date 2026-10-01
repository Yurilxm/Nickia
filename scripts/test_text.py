"""Testa pipeline de texto: normalizar -> pronuncia -> dividir."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from text import normalize, pronunciation, split
from config import MAX_CHARS_PER_SENTENCE


CASOS = [
    "Oi, pessoal! Hoje eu quero mostrar uma novidade linda que acabou de chegar na loja.",
    "Esse vestido est\u00e1 saindo por apenas R$ 89,90.",
    "Temos leggings e tops da cole\u00e7\u00e3o new arrivals.",
    "A blusa est\u00e1 com 30% de desconto s\u00f3 at\u00e9 domingo.",
    "Corre que s\u00e3o poucas pe\u00e7as! Temos do P ao GG e o frete \u00e9 gr\u00e1tis para todo o Brasil.",
    "Chama no WhatsApp para garantir a sua.",
]


def pipeline(texto: str) -> list:
    t = normalize.normalize(texto)
    t = pronunciation.apply(t)
    return split.split_sentences(t, MAX_CHARS_PER_SENTENCE)


def main():
    for i, caso in enumerate(CASOS, 1):
        print(f"\n--- Caso {i} ---")
        print(f"Original:   {caso}")
        t = normalize.normalize(caso)
        print(f"Normalize:  {t}")
        t = pronunciation.apply(t)
        print(f"Pronuncia:  {t}")
        frases = split.split_sentences(t, MAX_CHARS_PER_SENTENCE)
        for j, f in enumerate(frases, 1):
            print(f"  Frase {j}: {f}")


if __name__ == "__main__":
    main()
