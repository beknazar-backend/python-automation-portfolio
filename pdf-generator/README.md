# PDF Generator

Генератор PDF-документов для чеков и счётов на основе JSON-данных заказа.

## Установка

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Запуск

### Использование примера

```bash
python pdf_generator.py
```

Если в папке присутствует `sample_order.json`, он будет использован автоматически.

### Указание своего JSON-файла

```bash
python pdf_generator.py -i sample_order.json -o output/invoice.pdf
```

## Формат JSON

```json
{
  "customer_name": "ООО Поставщик",
  "document_number": "INV-2026-001",
  "date": "2026-05-15",
  "currency": "₽",
  "items": [
    { "name": "Товар A", "quantity": 2, "unit_price": 1500.00 },
    { "name": "Товар B", "quantity": 1, "unit_price": 2499.50 }
  ]
}
```

## Структура проекта

- `pdf_generator.py` — основной скрипт
- `sample_order.json` — пример данных заказа
- `requirements.txt` — зависимости
- `.gitignore` — правила Git

## Советы

- Убедитесь, что указали правильный путь к JSON-файлу
- При необходимости создавайте папку `output` заранее
- Проверяйте итоговый PDF после генерации
