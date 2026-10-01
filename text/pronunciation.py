"""Dicionario de pronuncia para termos estrangeiros/marcas."""
import json
import re
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parent.parent / "data" / "pronunciation.json"

DEFAULT = {
    "leggings": "l\u00e9guins",
    "top": "t\u00f3pi",
    "tops": "t\u00f3pis",
    "outfit": "autifit",
    "new arrivals": "niu arravals",
    "sale": "seil",
    "whatsapp": "uatsap",
    "instagram": "instagran",
    "look": "luque",
    "trend": "trend",
}


def load_rules() -> dict:
    if DICT_PATH.exists():
        return json.loads(DICT_PATH.read_text(encoding="utf-8-sig"))
    return dict(DEFAULT)


def save_rules(rules: dict) -> None:
    DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DICT_PATH.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply(texto: str, rules: dict = None) -> str:
    """Aplica substituicoes case-insensitive, palavra inteira."""
    rules = rules if rules is not None else load_rules()
    for chave in sorted(rules.keys(), key=len, reverse=True):
        valor = rules[chave]
        texto = re.sub(
            rf"\b{re.escape(chave)}\b",
            valor,
            texto,
            flags=re.IGNORECASE,
        )
    return texto
