"""Testes de normalizacao, split e pronuncia."""
from text import normalize, split, pronunciation


def test_moeda():
    assert "oitenta e nove reais" in normalize.normalize("R$ 89,90")
    assert "centavos" in normalize.normalize("R$ 89,90")


def test_moeda_milhar():
    out = normalize.normalize("R$ 1.234,56")
    assert "mil" in out
    assert "duzentos e trinta e quatro" in out


def test_moeda_real_singular():
    out = normalize.normalize("R$ 1")
    assert "um real" in out


def test_percentual():
    out = normalize.normalize("30% de desconto")
    assert "trinta por cento" in out


def test_numero_solto():
    assert "quarenta e dois" in normalize.normalize("tenho 42 pecas")


def test_split_pontuacao():
    frases = split.split_sentences("Oi, tudo bem? Tudo otimo. Obrigado!", 250)
    assert len(frases) == 3
    assert frases[0].endswith("?")
    assert frases[1].endswith(".")


def test_split_limite():
    frases = split.split_sentences("a " * 300, 100)
    assert all(len(f) <= 100 for f in frases)


def test_pronuncia_substitui():
    out = pronunciation.apply("leggings e tops", rules={"leggings": "leguins", "tops": "topis"})
    assert "leguins" in out
    assert "topis" in out


def test_pronuncia_case_insensitive():
    out = pronunciation.apply("LEGGINGS", rules={"leggings": "leguins"})
    assert out == "leguins"


def test_pronuncia_limite_palavra():
    out = pronunciation.apply("hiperleggings", rules={"leggings": "leguins"})
    assert out == "hiperleggings"
