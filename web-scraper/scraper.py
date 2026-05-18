import json
import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_page(url: str, headers: dict = None) -> BeautifulSoup:
    response = requests.get(url, headers=headers or {})
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value: str) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text


def parse_selector(element, selector: str):
    if not selector:
        return ""
    selector = selector.strip()
    if "@" in selector:
        css, attr = selector.split("@", 1)
        target = element.select_one(css)
        if not target:
            return ""
        if attr == "text":
            return clean_text(target.get_text())
        return clean_text(target.get(attr, ""))
    target = element.select_one(selector)
    return clean_text(target.get_text() if target else "")


def parse_products(page: BeautifulSoup, config: dict, base_url: str) -> list[dict]:
    items = []
    product_selector = config.get("product_selector")
    if not product_selector:
        raise ValueError("`product_selector` is required in config")
    product_blocks = page.select(product_selector)
    if not product_blocks:
        return []

    fields = config.get("fields", {})
    for block in product_blocks:
        row = {}
        for field_name, selector in fields.items():
            value = parse_selector(block, selector)
            if field_name == "link" and value:
                value = urljoin(base_url, value)
            if field_name == "price":
                value = normalize_price(value)
            row[field_name] = value
        if any(row.values()):
            items.append(row)
    return items


def normalize_price(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[^0-9,\.]", "", value)
    if cleaned.count(",") > 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", "")
    cleaned = cleaned.replace(" ", "")
    if "," in cleaned and cleaned.rfind(",") > cleaned.rfind("."):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    return cleaned


def find_next_page(page: BeautifulSoup, config: dict, base_url: str) -> str | None:
    next_selector = config.get("next_page_selector")
    if not next_selector:
        return None
    next_item = page.select_one(next_selector)
    if not next_item:
        return None
    if next_item.name == "a":
        return urljoin(base_url, next_item.get("href", ""))
    href = next_item.get("href") or next_item.get("data-href")
    return urljoin(base_url, href) if href else None


def save_to_excel(items: list[dict], output_file: Path) -> None:
    df = pd.DataFrame(items)
    df = df[[col for col in ["name", "price", "link", "availability"] if col in df.columns]] if not df.empty else df
    df.to_excel(output_file, index=False)


def main() -> None:
    config = load_config(CONFIG_PATH)
    start_url = config.get("start_url")
    if not start_url:
        raise ValueError("`start_url` is required in config")

    headers = config.get("headers", {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    output_file = Path(config.get("output_file", "prices.xlsx"))
    collected = []
    current_url = start_url
    visited = set()

    while current_url and current_url not in visited:
        print(f"Fetching: {current_url}")
        page = fetch_page(current_url, headers)
        visited.add(current_url)
        collected.extend(parse_products(page, config, current_url))
        current_url = find_next_page(page, config, current_url)

    cleaned = [row for row in collected if any(str(value).strip() for value in row.values())]
    if not cleaned:
        print("No products found. Check your selectors in config.json.")
        return

    save_to_excel(cleaned, output_file)
    print(f"Saved {len(cleaned)} rows to {output_file}")


if __name__ == "__main__":
    main()
