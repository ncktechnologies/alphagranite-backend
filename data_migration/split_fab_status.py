"""Move every FAB row with complete=false out of an export."""
import argparse
import codecs
import csv
import os
from pathlib import Path
import shutil
import tempfile


FALSE_VALUES = {"0", "false", "no", "n", "f"}


def split_csv(source: Path, output: Path, *, apply: bool = False) -> tuple[int, int]:
    source = source.resolve()
    output = output.resolve()
    backup = source.with_suffix(source.suffix + ".bak")
    if output == source or output.parent == source.parent:
        raise ValueError("The moved-rows file must be outside the source CSV directory.")

    with source.open("rb") as stream:
        encoding = "utf-8-sig" if stream.read(3) == codecs.BOM_UTF8 else "utf-8"
    with source.open(encoding=encoding, newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if not header:
            raise ValueError("The source CSV is empty.")
        names = [name.strip().lower() for name in header]
        if names.count("complete") != 1:
            raise ValueError("Expected exactly one 'complete' column.")
        complete_column = names.index("complete")
        kept = []
        moved = []
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"CSV record {row_number} has an unexpected column count.")
            matches = row[complete_column].strip().lower() in FALSE_VALUES
            (moved if matches else kept).append(row)

    if not apply or not moved:
        return len(kept), len(moved)
    if backup.exists() or output.exists():
        raise FileExistsError("Backup or moved-rows file already exists; refusing to overwrite it.")

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, newline="", dir=source.parent,
            prefix=source.name + ".", suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(kept)
        shutil.copymode(source, temporary_path)
        with backup.open("xb") as destination, source.open("rb") as original:
            shutil.copyfileobj(original, destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding=encoding, newline="") as stream:
            writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(moved)
        os.replace(temporary_path, source)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return len(kept), len(moved)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Fab_Status CSV to filter")
    parser.add_argument("--output", type=Path, help="Destination outside the source CSV directory")
    parser.add_argument("--apply", action="store_true", help="Back up and rewrite the source; default is preview only")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output or source.parent.parent / "excluded_fab_status" / source.name
    try:
        kept, moved = split_csv(source, output, apply=args.apply)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Rows kept: {kept}; rows to move: {moved}")
    print("Rule: complete=false, regardless of fab_percent.")
    if args.apply and moved:
        print(f"Updated source: {source}")
        print(f"Moved rows: {output.resolve()}")
        print(f"Original backup: {source.with_suffix(source.suffix + '.bak')}")
    else:
        print("No files changed." if args.apply else "Preview only. Run again with --apply to move these rows.")


if __name__ == "__main__":
    main()