import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from fpdf import FPDF
except ModuleNotFoundError:
    print("Зависимость 'fpdf2' не найдена. Устанавливаю автоматически...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    except subprocess.CalledProcessError:
        raise SystemExit("Не удалось установить пакет fpdf2. Запустите: python -m pip install fpdf2")
    from fpdf import FPDF


@dataclass
class OrderItem:
    name: str
    quantity: int
    unit_price: float

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    customer_name: str
    document_number: str
    date: str
    items: List[OrderItem] = field(default_factory=list)
    currency: str = "₸"
    document_title: str = "Счет / Чек"

    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)


class InvoicePDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_name = "Helvetica"
        self.document_title = "Счет / Чек"

    def header(self):
        self.set_font(self.font_name, "B", 16)
        self.set_text_color(33, 37, 41)
        self.cell(0, 10, self.document_title, border=False, ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font(self.font_name, "I", 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Сгенерировано: {datetime.now():%Y-%m-%d %H:%M}", 0, 0, "C")

    def add_order_info(self, order: Order):
        self.set_font(self.font_name, "", 11)
        self.set_text_color(33, 37, 41)
        self.cell(0, 6, f"Клиент: {order.customer_name}", ln=True)
        self.cell(0, 6, f"Номер документа: {order.document_number}", ln=True)
        self.cell(0, 6, f"Дата: {order.date}", ln=True)
        self.ln(6)

    def add_items_table(self, order: Order):
        self.set_font(self.font_name, "B", 11)
        self.set_fill_color(240, 240, 240)
        self.cell(80, 8, "Товар", border=1, fill=True)
        self.cell(25, 8, "Кол-во", border=1, fill=True, align="C")
        self.cell(35, 8, "Цена", border=1, fill=True, align="R")
        self.cell(35, 8, "Сумма", border=1, fill=True, align="R")
        self.ln()

        self.set_font(self.font_name, "", 11)
        for item in order.items:
            self.cell(80, 8, item.name, border=1)
            self.cell(25, 8, str(item.quantity), border=1, align="C")
            self.cell(35, 8, format_currency(item.unit_price, order.currency), border=1, align="R")
            self.cell(35, 8, format_currency(item.total_price, order.currency), border=1, align="R")
            self.ln()

        self.set_font(self.font_name, "B", 12)
        self.cell(140, 10, "Итого:", border=1)
        self.cell(35, 10, format_currency(order.total_amount, order.currency), border=1, align="R")
        self.ln(15)

    def add_footer_note(self):
        self.set_font(self.font_name, "I", 10)
        self.set_text_color(120)
        self.multi_cell(0, 6, "Спасибо за покупку! Этот документ сформирован автоматически.")


def format_currency(amount: float, currency: str) -> str:
    return f"{amount:,.2f} {currency}".replace(",", " ").replace(".", ",")


def get_json_value(data: dict, keys: List[str], default=None):
    for key in keys:
        if key in data:
            return data[key]
    return default


def load_order_from_json(path: Path) -> Order:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    items_data = get_json_value(data, ["items", "products", "товары"], [])
    items = []
    for item in items_data:
        item_name = get_json_value(item, ["name", "title", "description", "товар", "название"], "")
        quantity = get_json_value(item, ["quantity", "qty", "count", "количество"], 1)
        unit_price = get_json_value(item, ["unit_price", "price", "unitPrice", "cost", "цена", "стоимость"], 0)
        items.append(OrderItem(
            name=str(item_name),
            quantity=int(quantity) if quantity is not None else 1,
            unit_price=float(unit_price if unit_price is not None else 0),
        ))

    return Order(
        customer_name=str(get_json_value(data, ["customer_name", "client_name", "buyer", "покупатель", "клиент"], "Покупатель")),
        document_number=str(get_json_value(data, ["document_number", "doc_number", "invoice_number", "number", "номер"], "")),
        date=str(get_json_value(data, ["date", "document_date", "issue_date", "дата"], datetime.now().strftime("%Y-%m-%d"))),
        items=items,
        currency=str(get_json_value(data, ["currency", "валюта", "currency_symbol"], "₸")),
        document_title=str(get_json_value(data, ["document_title", "title", "header", "заголовок"], "Счет / Чек")),
    )


def find_unicode_fonts() -> dict[str, Path]:
    """Find Unicode fonts for Cyrillic/Kazakh text on common systems."""
    font_sets = [
        {
            "": Path("C:/Windows/Fonts/arial.ttf"),
            "B": Path("C:/Windows/Fonts/arialbd.ttf"),
            "I": Path("C:/Windows/Fonts/ariali.ttf"),
        },
        {
            "": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            "B": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            "I": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        },
        {
            "": Path("/Library/Fonts/Arial Unicode.ttf"),
            "B": Path("/Library/Fonts/Arial Unicode.ttf"),
            "I": Path("/Library/Fonts/Arial Unicode.ttf"),
        },
    ]
    for fonts in font_sets:
        if all(path.exists() for path in fonts.values()):
            return fonts
    return {}


def generate_pdf(order: Order, output_path: Path) -> None:
    pdf = InvoicePDF(format="A4")
    pdf.document_title = order.document_title
    fonts = find_unicode_fonts()
    if fonts:
        for style, font_path in fonts.items():
            pdf.add_font("Unicode", style, str(font_path))
        pdf.font_name = "Unicode"
    else:
        raise RuntimeError(
            "Unicode font not found. Install Arial or DejaVu Sans to generate PDF with Cyrillic/Kazakh text."
        )

    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.add_order_info(order)
    pdf.add_items_table(order)
    pdf.add_footer_note()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))


def create_sample_order() -> Order:
    return Order(
        customer_name="ООО Поставщик",
        document_number="INV-2026-001",
        date=datetime.now().strftime("%Y-%m-%d"),
        currency="₸",
        items=[
            OrderItem(name="Товар A", quantity=2, unit_price=1500.00),
            OrderItem(name="Товар B", quantity=1, unit_price=2499.50),
            OrderItem(name="Товар C", quantity=3, unit_price=799.90),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Генератор PDF документов (чеки / счета)")
    parser.add_argument("-i", "--input", type=Path, help="Путь к JSON-файлу с данными заказа")
    parser.add_argument("-o", "--output", type=Path, default=Path("output/invoice.pdf"), help="Путь к выходному PDF файлу")
    args = parser.parse_args()

    if args.input is None:
        default_json = Path("sample_order.json")
        if default_json.exists():
            args.input = default_json

    if args.input:
        order = load_order_from_json(args.input)
    else:
        order = create_sample_order()

    generate_pdf(order, args.output)
    print(f"PDF успешно создан: {args.output}")


if __name__ == "__main__":
    main()
