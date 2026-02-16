"""Testy format_translations_display (ręczne tłumaczenia w kolejności tablicy)."""
import NeoAnki


def test_format_translations_display_with_translations():
    table = [("a", "A"), ("b", "bb"), ("c", "")]
    out = NeoAnki.format_translations_display(table)
    assert "  a: A" in out
    assert "  b: bb" in out
    assert "  c: (brak tłumaczenia)" in out
    assert out.strip().count("\n") == 2


def test_format_translations_display_preserves_order():
    table = [("z", "zz"), ("y", ""), ("x", "xx")]
    out = NeoAnki.format_translations_display(table)
    lines = [ln.strip() for ln in out.strip().split("\n")]
    assert lines[0] == "z: zz"
    assert lines[1] == "y: (brak tłumaczenia)"
    assert lines[2] == "x: xx"


def test_format_translations_display_empty_table():
    assert NeoAnki.format_translations_display([]) == ""


def test_format_translations_display_all_missing():
    table = [("p", ""), ("q", "")]
    out = NeoAnki.format_translations_display(table)
    assert "(brak tłumaczenia)" in out
    assert out.count("(brak tłumaczenia)") == 2
