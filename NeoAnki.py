import random
import os
import json
import sys
from datetime import datetime

import questionary

BACKUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neoanki_backup.json")


def load_backup() -> dict[str, list[str]]:
    if not os.path.exists(BACKUP_PATH):
        return {}
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_backup(boards: dict[str, list[str]]) -> None:
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(boards, f, ensure_ascii=False, indent=2)


def getInputTable():
    clearScreen()
    wordsInput = input("Wypisz słowa oddzielone przecinkiem: \n")
    wordsInput = wordsInput.split(",")
    table = [word.strip() for word in wordsInput]
    return table


def clearScreen():
    os.system("cls" if sys.platform == "win32" else "clear")


def getShuffledTable(table: list):
    clearScreen()
    random.shuffle(table)
    return table


def backup_submenu(
    current_table: list[str],
    current_name: str | None,
    used_boards: dict[str, list[str]],
) -> tuple[list[str], str | None, dict[str, list[str]]]:
    clearScreen()
    label = f"Obecna tablica: {current_name or '(bez nazwy)'}"
    print(label)
    print(", ".join(current_table) if current_table else "(pusta)")
    print()
    choice = questionary.select(
        "Backup:",
        choices=["Wyciągnij tablicę", "Zapisz obecną", "Usuń nieużywane", "Wstecz"],
    ).ask()
    if not choice or choice == "Wstecz":
        return current_table, current_name, used_boards

    if choice == "Wyciągnij tablicę":
        backup = load_backup()
        if not backup:
            clearScreen()
            input("Brak zapisanych tablic. Enter...")
            return current_table, current_name, used_boards
        clearScreen()
        print("Obecna:", ", ".join(current_table) if current_table else "(pusta)\n")
        name = questionary.select("Którą tablicę?", choices=list(backup.keys())).ask()
        if name:
            used_boards[name] = backup[name]
            return backup[name], name, used_boards

    if choice == "Zapisz obecną":
        clearScreen()
        print("Obecna tablica:", ", ".join(current_table) if current_table else "(pusta)\n")
        base = questionary.text("Nazwa tablicy (opcjonalnie):").ask()
        stamp = datetime.now().strftime("%Y-%m-%d %H-%M")
        name = f"{base} {stamp}".strip() if base else stamp
        if name:
            used_boards[name] = current_table
            backup = load_backup()
            backup[name] = current_table
            save_backup(backup)
            return current_table, name, used_boards

    if choice == "Usuń nieużywane":
        backup = load_backup()
        used_names = set(used_boards.keys())
        to_remove_keys = [k for k in backup if k not in used_names]
        if not to_remove_keys:
            clearScreen()
            input("Wszystkie zapisane tablice są używane. Enter...")
            return current_table, current_name, used_boards
        choices = [
            questionary.Choice(title=f"{k} | {', '.join(backup[k][:8])}{'...' if len(backup[k]) > 8 else ''}", value=k)
            for k in to_remove_keys
        ]
        selected = questionary.checkbox("Które tablice usunąć?", choices=choices).ask()
        if selected:
            for k in selected:
                del backup[k]
            save_backup(backup)
            clearScreen()
            input(f"Usunięto z backupu: {', '.join(selected)}. Enter...")

    return current_table, current_name, used_boards


clearScreen()
start = questionary.select(
    "Co chcesz zrobić?",
    choices=["Wpisz tablicę", "Przejdź do menu"],
).ask()
current_table = getInputTable() if start == "Wpisz tablicę" else []
current_name: str | None = None
used_boards: dict[str, list[str]] = {}

while True:
    clearScreen()
    choice = questionary.select(
        "Wybierz:",
        choices=["Wymieszaj", "Nowa tablica", "Backup", "Wyjście"],
    ).ask()
    if not choice or choice == "Wyjście":
        exit()
    if choice == "Wymieszaj":
        while True:
            current_table = getShuffledTable(current_table)
            print(", ".join(current_table))
            again = questionary.select(
                "\nCo dalej?",
                choices=["Wymieszaj ponownie", "Wróć do menu"],
            ).ask()
            if not again or again == "Wróć do menu":
                break
        continue
    if choice == "Nowa tablica":
        current_table = getInputTable()
        current_name = None
        continue
    if choice == "Backup":
        current_table, current_name, used_boards = backup_submenu(
            current_table, current_name, used_boards
        )
        continue
