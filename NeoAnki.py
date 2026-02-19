import random
import os
import json
import subprocess
import sys
import tempfile
from datetime import datetime

import questionary

BACKUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neoanki_backup.json")
BACKUP_BACKUP_PATH = BACKUP_PATH + ".bak"

# ANSI: bold + color for backup list titles
_BOLD_CYAN = "\033[1m\033[36m"
_RESET = "\033[0m"

# Table = list of pairs (word, translation). Translation can be "".
TableRow = tuple[str, str]
Table = list[TableRow]


def _row_to_display(row: TableRow | str) -> str:
    """Accepts (word, trans) or legacy: single string (treated as word without translation)."""
    if isinstance(row, str):
        return row
    w, t = row
    return f"{w} ({t})" if t else w


def _table_display(table: Table, max_items: int | None = None) -> str:
    part = table[:max_items] if max_items else table
    return ", ".join(_row_to_display(r) for r in part) + ("..." if max_items and len(table) > max_items else "")


def _table_display_words_only(table: Table, max_items: int | None = None) -> str:
    """Words only (no translations) — for shuffle view."""
    part = table[:max_items] if max_items else table
    return ", ".join(r[0] for r in part) + ("..." if max_items and len(table) > max_items else "")


def _table_display_with_revealed(table: Table, revealed: int) -> str:
    """Numbered list: first `revealed` with translation, rest word only."""
    if not table:
        return "(empty)"
    width = len(str(len(table)))
    lines = [
        f"  {i + 1:>{width}}. " + (_row_to_display(r) if i < revealed else r[0])
        for i, r in enumerate(table)
    ]
    header = "─" * (width + 4)
    return f"  {header}\n" + "\n".join(lines) + f"\n  {header}"


def _print_backup_list(backup: dict[str, Table]) -> None:
    """Prints backup list: title (bold, colored), below table elements."""
    for name in sorted(backup.keys()):
        table = backup[name]
        print(f"{_BOLD_CYAN}{name}{_RESET}")
        for word, trans in table:
            print(f"    {word}: {trans if trans else '(no translation)'}")
        print()


def format_translations_display(table: Table) -> str:
    """Returns display text: each row '  word: trans' or '  word: (no translation)' in table order."""
    lines = [
        f"  {word}: {trans if trans else '(no translation)'}"
        for word, trans in table
    ]
    return "\n".join(lines)


def _parse_table_cell(cell: str) -> TableRow:
    cell = cell.strip()
    if "|" in cell:
        w, _, t = cell.partition("|")
        return (w.strip(), t.strip())
    return (cell, "")


def _validate_backup(data: object) -> dict[str, list[list[str]]] | None:
    """Accepts dict: values are lists of strings (old format) or lists [word, trans]. Returns normalized [word, trans] lists."""
    if not isinstance(data, dict):
        return None
    out: dict[str, list[list[str]]] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, list):
            return None
        rows: list[list[str]] = []
        for x in v:
            if isinstance(x, str):
                rows.append([x, ""])
            elif isinstance(x, list) and len(x) == 2 and isinstance(x[0], str) and isinstance(x[1], str):
                rows.append([x[0], x[1]])
            else:
                return None
        out[k] = rows
    return out


def _backup_to_table(rows: list[list[str]]) -> Table:
    return [ (r[0], r[1]) for r in rows ]


def _table_to_backup(table: Table) -> list[list[str]]:
    return [ [w, t] for w, t in table ]


def _validate_table(table: object) -> bool:
    """Checks if this is a Table (list of pairs (str, str))."""
    if not isinstance(table, list):
        return False
    for row in table:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            return False
        if not isinstance(row[0], str) or not isinstance(row[1], str):
            return False
    return True


def _read_backup_file(path: str) -> dict[str, list[list[str]]] | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _validate_backup(data)
    except (json.JSONDecodeError, OSError):
        return None


def load_backup() -> tuple[dict[str, Table], bool]:
    """Loads backup; if main file is corrupted tries .bak. Repairs main from .bak if needed.
    Returns (data, recovered_from_bak)."""
    main_data = _read_backup_file(BACKUP_PATH)
    if main_data is not None:
        return {k: _backup_to_table(v) for k, v in main_data.items()}, False
    bak_data = _read_backup_file(BACKUP_BACKUP_PATH)
    if bak_data is not None:
        try:
            with open(BACKUP_PATH, "w", encoding="utf-8") as f:
                json.dump(bak_data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        return {k: _backup_to_table(v) for k, v in bak_data.items()}, True
    return {}, False


def save_backup(boards: dict[str, Table]) -> None:
    """Saves backup: first copy main→.bak, then save to main (via temp file)."""
    if not isinstance(boards, dict):
        raise ValueError("Invalid backup structure")
    for k, v in boards.items():
        if not isinstance(k, str) or not _validate_table(v):
            raise ValueError("Invalid backup structure")
    serialized = {k: _table_to_backup(v) for k, v in boards.items()}
    if _validate_backup(serialized) is None:
        raise ValueError("Invalid backup structure")
    if os.path.exists(BACKUP_PATH):
        try:
            with open(BACKUP_PATH, "r", encoding="utf-8") as f:
                prev = f.read()
            with open(BACKUP_BACKUP_PATH, "w", encoding="utf-8") as f:
                f.write(prev)
        except OSError:
            pass
    fd, tmp = tempfile.mkstemp(suffix=".json", dir=os.path.dirname(BACKUP_PATH) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)
        os.replace(tmp, BACKUP_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _confirm_table(table: Table) -> bool:
    """Shows table and asks for confirmation. Returns True if user confirms."""
    if not table:
        return False
    clearScreen()
    print("Table:\n")
    print(_table_display_with_revealed(table, len(table)))
    print()
    return questionary.select("Confirm table?", choices=["Yes", "No"]).ask() == "Yes"


def getInputTableSingle() -> Table:
    """Add words one by one (word + Enter). Empty Enter = finish. Confirmation at the end."""
    table: Table = []
    while True:
        clearScreen()
        if table:
            print(f"Word count: {len(table)}\nAdd empty word to finish")
            print(_table_display_with_revealed(table, len(table)))
            print()
        prompt = "Word|translation (empty Enter = finish): "
        line = input(prompt).strip()
        if not line:
            break
        table.append(_parse_table_cell(line))
    if not table:
        return []
    return table if _confirm_table(table) else []


def getInputTableAllAtOnce() -> Table:
    """All elements at once (comma-separated). Confirmation at the end."""
    clearScreen()
    prompt = "Enter elements (element|translation separated by comma)\nExample: word|translation,word1|translation1,word2,word3|trans3\nTranslations are optional\n"
    raw = input(prompt)
    table = [_parse_table_cell(cell) for cell in raw.split(",") if cell.strip()]
    return table if _confirm_table(table) else []


def getInputTable() -> Table:
    """Asks for mode (one by one / all at once) and returns table after confirmation."""
    clearScreen()
    mode = questionary.select(
        "How to add words?",
        choices=["One by one (word by word)", "All at once (comma-separated)"],
    ).ask()
    if not mode:
        return []
    if mode == "One by one (word by word)":
        return getInputTableSingle()
    return getInputTableAllAtOnce()


def clearScreen():
    os.system("cls" if sys.platform == "win32" else "clear")


def getShuffledTable(table: list):
    clearScreen()
    random.shuffle(table)
    return table


def backup_submenu(
    current_table: Table,
    current_name: str | None,
    used_boards: dict[str, Table],
) -> tuple[Table, str | None, dict[str, Table]]:
    clearScreen()
    label = f"Current table: {current_name or '(unnamed)'}"
    print(label)
    print(_table_display(current_table) if current_table else "(empty)")
    print()
    choice = questionary.select(
        "Backup:",
        choices=["Load table", "Save current", "Edit table", "Delete tables", "Back"],
    ).ask()
    if not choice or choice == "Back":
        return current_table, current_name, used_boards

    if choice == "Load table":
        backup, _ = load_backup()
        if not backup:
            clearScreen()
            input("No saved tables. Enter...")
            return current_table, current_name, used_boards
        clearScreen()
        _print_backup_list(backup)
        name = questionary.select("Which table to load?", choices=sorted(backup.keys())).ask()
        if name:
            used_boards[name] = backup[name]
            return backup[name], name, used_boards

    if choice == "Save current":
        backup, _ = load_backup()
        clearScreen()
        _print_backup_list(backup)
        choices_save = ["[new table]"] + sorted(backup.keys())
        target = questionary.select("Save as (new or overwrite selected):", choices=choices_save).ask()
        if not target:
            return current_table, current_name, used_boards
        if target == "[new table]":
            base = questionary.text("Table name (optional):").ask()
            stamp = datetime.now().strftime("%Y-%m-%d %H-%M")
            name = f"{base} {stamp}".strip() if base else stamp
            if name:
                used_boards[name] = current_table
                backup, _ = load_backup()
                backup[name] = current_table
                save_backup(backup)
                return current_table, name, used_boards
        else:
            name = target
            backup[name] = current_table
            save_backup(backup)
            used_boards[name] = current_table
            clearScreen()
            input(f"Overwritten: {name}. Enter...")
            return current_table, name, used_boards

    if choice == "Edit table":
        backup, _ = load_backup()
        if not backup:
            clearScreen()
            input("No saved tables. Enter...")
            return current_table, current_name, used_boards
        clearScreen()
        _print_backup_list(backup)
        name = questionary.select("Which table to edit?", choices=sorted(backup.keys())).ask()
        if not name:
            return current_table, current_name, used_boards
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(", ".join(f"{w}|{t}" if t else w for w, t in backup[name]))
            path = f.name
        try:
            editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "nano")
            subprocess.run([editor, path], shell=(sys.platform == "win32"))
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
        finally:
            os.unlink(path)
        new_table = [_parse_table_cell(cell) for cell in raw.split(",") if cell.strip()]
        backup[name] = new_table
        save_backup(backup)
        if current_name == name:
            current_table = new_table
        if name in used_boards:
            used_boards[name] = new_table
        clearScreen()
        input(f"Saved: {name}. Enter...")

    if choice == "Delete tables":
        backup, _ = load_backup()
        if not backup:
            clearScreen()
            input("No saved tables. Enter...")
            return current_table, current_name, used_boards
        clearScreen()
        _print_backup_list(backup)
        print("Select: Space. Confirm: Enter. To go back without deleting: select nothing and Enter.")
        print()
        choices = [
            questionary.Choice(title=f"{k} | {_table_display(backup[k], 8)}", value=k)
            for k in sorted(backup.keys())
        ]
        selected = questionary.checkbox("Which tables to delete?", choices=choices).ask()
        if selected is None:
            return current_table, current_name, used_boards
        if not selected:
            clearScreen()
            input("Cancelled (nothing deleted). Enter...")
            return current_table, current_name, used_boards
        confirm = questionary.select(
            f"Delete {len(selected)} table(s) from backup?",
            choices=["Yes, delete", "No, go back"],
        ).ask()
        if confirm == "Yes, delete":
            for k in selected:
                del backup[k]
            save_backup(backup)
            clearScreen()
            input(f"Deleted from backup: {', '.join(selected)}. Enter...")

    return current_table, current_name, used_boards


def main() -> None:
    clearScreen()
    _, recovered = load_backup()
    if recovered:
        print("Recovered backup from .bak file (main file was corrupted).")
        input("Enter...")
        clearScreen()
    start = questionary.select(
        "What do you want to do?",
        choices=["Enter table", "Load table from backup", "Go to menu"],
    ).ask()
    if start == "Enter table":
        current_table = getInputTable()
        current_name = None
    elif start == "Load table from backup":
        backup, _ = load_backup()
        if not backup:
            clearScreen()
            input("No saved tables. Enter...")
            current_table = []
            current_name = None
        else:
            clearScreen()
            _print_backup_list(backup)
            name = questionary.select("Which table to load?", choices=sorted(backup.keys())).ask()
            if name:
                current_table = backup[name]
                current_name = name
            else:
                current_table = []
                current_name = None
    else:
        current_table = []
        current_name = None
    used_boards: dict[str, Table] = {}
    if current_name:
        used_boards[current_name] = current_table

    while True:
        clearScreen()
        menu_choices = ["New table", "Backup", "Exit"]
        if current_table:
            menu_choices.insert(0, "Shuffle")
        choice = questionary.select("Choose:", choices=menu_choices).ask()
        if not choice or choice == "Exit":
            return
        if choice == "Shuffle":
            while True:
                current_table = getShuffledTable(current_table)
                revealed_count = 0
                while True:
                    clearScreen()
                    print(_table_display_with_revealed(current_table, revealed_count))
                    if revealed_count < len(current_table):
                        choices_list = ["Show all translations", "Shuffle again", "Remove element", "Back to menu"]
                        choices_list.insert(0, "Show next translation")
                    else:
                        choices_list = ["Shuffle again", "Show all translations", "Remove element", "Back to menu"]
                    again = questionary.select("\nWhat next?", choices=choices_list).ask()
                    if not again or again == "Back to menu":
                        break
                    if again == "Shuffle again":
                        break
                    if again == "Show next translation":
                        if revealed_count < len(current_table):
                            revealed_count += 1
                        continue
                    if again == "Show all translations" and current_table:
                        clearScreen()
                        print("Order as after shuffle:\n")
                        print(format_translations_display(current_table))
                        input("\nEnter...")
                    if again == "Remove element":
                        if not current_table:
                            input("Table empty. Enter...")
                            continue
                        choices = [
                            questionary.Choice(title=_row_to_display(r), value=i)
                            for i, r in enumerate(current_table)
                        ] + [questionary.Choice(title="Cancel", value=None)]
                        to_remove = questionary.select("Which element to remove?", choices=choices).ask()
                        if to_remove is not None:
                            current_table.pop(to_remove)
                            revealed_count = min(revealed_count, len(current_table))
                if again == "Back to menu":
                    break
            continue
        if choice == "New table":
            current_table = getInputTable()
            current_name = None
            continue
        if choice == "Backup":
            current_table, current_name, used_boards = backup_submenu(
                current_table, current_name, used_boards
            )
            continue


if __name__ == "__main__":
    main()
