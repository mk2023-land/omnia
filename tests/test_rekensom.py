import pytest

from app.core.rekensom import VOORBEELD, WEKEN_PER_MAAND, bereken


def test_voorbeeld_klopt():
    # 60 oproepen/week, 25% gemist, 50% wordt klus, EUR 250 per klus
    uitkomst = bereken(**VOORBEELD)
    verwacht = 60 * WEKEN_PER_MAAND * 0.25 * 0.5 * 250
    assert uitkomst["omzet_per_maand"] == round(verwacht)
    assert uitkomst["gemist_per_maand"] == 65.0
    assert uitkomst["omzet_per_jaar"] == round(verwacht * 12)


def test_niets_gemist_is_nul():
    assert bereken(100, 0, 500)["omzet_per_maand"] == 0


def test_aannames_staan_erbij():
    aannames = bereken(10, 10, 100, deel_klus_pct=30)["aannames"]
    assert any("30%" in a for a in aannames)
    assert any("weken" in a for a in aannames)


@pytest.mark.parametrize("args", [(-1, 10, 100), (10, 101, 100), (10, 10, -5)])
def test_onzin_wordt_geweigerd(args):
    with pytest.raises(ValueError):
        bereken(*args)
