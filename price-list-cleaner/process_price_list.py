import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd

DEFAULT_NAME_PATTERNS = ["name", "title", "product", "item", "товар", "наименование"]
DEFAULT_PRICE_PATTERNS = ["price", "cost", "цена", "price_", "cost_"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Очистка и нормализации прайс-листов (Excel/CSV) для загрузки в интернет-магазин."
    )
    parser.add_argument("input", help="Входной файл CSV или Excel")
    parser.add_argument("output", help="Выходной файл CSV или Excel")
    parser.add_argument("--sheet", help="Имя листа Excel (по умолчанию первый)")
    parser.add_argument("--delimiter", default=",", help="Разделитель для CSV файлов (по умолчанию ',')")
    parser.add_argument("--price-cols", nargs="+", help="Названия колонок с ценами")
    parser.add_argument("--name-col", help="Название колонки с наименованием товара")
    parser.add_argument("--markup", type=float, default=0.0, help="Наценка в процентах, например 10 для +10%%")
    parser.add_argument(
        "--rename-map",
        help="JSON строка или путь к JSON/CSV файлу с переименованиями (old:new).",
    )
    parser.add_argument(
        "--drop-cols",
        nargs="*",
        default=[],
        help="Список колонок, которые нужно удалить из итогового файла.",
    )
    parser.add_argument(
        "--keep-cols",
        nargs="*",
        help="Если указан, сохраняются только эти колонки.",
    )
    return parser.parse_args()


def read_input(path: Path, sheet: str | None, delimiter: str) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xls", ".xlsx", ".xlsm", ".xlsb"}:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    if suffix == ".csv":
        return pd.read_csv(path, delimiter=delimiter, dtype=str)
    raise ValueError(f"Неподдерживаемый формат файла: {path}")


def infer_columns(columns, patterns):
    lower_cols = [c.lower() for c in columns]
    matches = [c for c in columns if any(p in c.lower() for p in patterns)]
    return matches


def normalize_string(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if value == "":
        return value
    return value


def normalize_name(value: str) -> str:
    value = normalize_string(value)
    if value == "":
        return value
    # keep numbers and uppercase acronyms as-is where possible
    return value.title()


def normalize_price(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value)
    value = value.strip()
    if value == "":
        return None
    # Удаляем все символы, кроме цифр, точек и запятых
    value = re.sub(r"[^0-9,\.\-]", "", value)
    if value.count(",") > 1 and value.count(".") == 0:
        value = value.replace(",", "")
    elif value.count(",") == 1 and value.count(".") == 0:
        value = value.replace(",", ".")
    value = value.replace(" ", "")
    try:
        return float(value)
    except ValueError:
        return None


def load_rename_map(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        if os.path.exists(raw):
            path = Path(raw)
            if path.suffix.lower() == ".json":
                return json.loads(path.read_text(encoding="utf-8"))
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(path, header=None, names=["old", "new"], dtype=str)
                return dict(df.dropna().values)
        return json.loads(raw)
    except Exception as exc:
        raise ValueError(f"Не удалось загрузить карту переименований: {exc}")


def apply_rename_map(value, rename_map: dict[str, str]):
    if not isinstance(value, str):
        return value
    key = value.strip()
    if key in rename_map:
        return rename_map[key]
    for old, new in rename_map.items():
        if old.lower() in key.lower():
            return re.sub(re.escape(old), new, key, flags=re.IGNORECASE)
    return value


def clean_dataframe(df: pd.DataFrame, args):
    df = df.copy()
    df.columns = [normalize_string(str(col)) for col in df.columns]

    if args.keep_cols:
        keep = [normalize_string(c) for c in args.keep_cols]
        df = df[[col for col in df.columns if col in keep]]

    if args.drop_cols:
        drop = [normalize_string(c) for c in args.drop_cols]
        df = df.drop(columns=[col for col in df.columns if col in drop], errors="ignore")

    df = df.dropna(how="all")
    df = df.drop_duplicates()

    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].astype(str).map(normalize_string)
        df[col] = df[col].replace({"nan": None})

    price_cols = args.price_cols
    if not price_cols:
        price_cols = infer_columns(df.columns, DEFAULT_PRICE_PATTERNS)
    if price_cols:
        for col in price_cols:
            if col in df.columns:
                df[col] = df[col].map(normalize_price)
                if args.markup:
                    df[col] = df[col].astype(float, errors="ignore").map(
                        lambda value: None
                        if value is None or pd.isna(value)
                        else round(value * (1 + args.markup / 100.0), 2)
                    )

    if args.name_col and args.name_col in df.columns:
        name_col = args.name_col
    else:
        names = infer_columns(df.columns, DEFAULT_NAME_PATTERNS)
        name_col = names[0] if names else None

    rename_map = load_rename_map(args.rename_map)
    if name_col and name_col in df.columns:
        df[name_col] = df[name_col].map(lambda v: apply_rename_map(normalize_name(v), rename_map))
    else:
        if rename_map:
            for col in df.columns:
                df[col] = df[col].map(lambda v: apply_rename_map(v, rename_map))

    return df


def write_output(df: pd.DataFrame, path: Path):
    suffix = path.suffix.lower()
    if suffix in {".xls", ".xlsx", ".xlsm", ".xlsb"}:
        df.to_excel(path, index=False)
    elif suffix == ".csv":
        df.to_csv(path, index=False)
    else:
        raise ValueError(f"Неподдерживаемый формат выходного файла: {path}")


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Входной файл не найден: {input_path}")

    df = read_input(input_path, args.sheet, args.delimiter)
    cleaned = clean_dataframe(df, args)
    write_output(cleaned, output_path)
    print(f"Готовый прайс-лист сохранен в: {output_path}")


if __name__ == "__main__":
    main()
