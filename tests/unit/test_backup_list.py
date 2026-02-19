"""Tests for _print_backup_list (alphabetical order, title + elements)."""
import NeoAnki


def test_print_backup_list_sorted_order(capsys):
    backup = {
        "zeta": [("z", "")],
        "alfa": [("a", "")],
        "beta": [("b", "B")],
    }
    NeoAnki._print_backup_list(backup)
    out = capsys.readouterr().out
    # Kolejność alfabetyczna: alfa, beta, zeta
    pos_alfa = out.index("alfa")
    pos_beta = out.index("beta")
    pos_zeta = out.index("zeta")
    assert pos_alfa < pos_beta < pos_zeta


def test_print_backup_list_contains_titles_and_elements(capsys):
    backup = {"Lista1": [("słowo", "tłum")]}
    NeoAnki._print_backup_list(backup)
    out = capsys.readouterr().out
    assert "Lista1" in out
    assert "słowo" in out
    assert "tłum" in out


def test_print_backup_list_no_translation(capsys):
    backup = {"X": [("w", "")]}
    NeoAnki._print_backup_list(backup)
    out = capsys.readouterr().out
    assert "(no translation)" in out


def test_print_backup_list_empty_dict(capsys):
    NeoAnki._print_backup_list({})
    out = capsys.readouterr().out
    assert out == ""
