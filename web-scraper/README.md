# Web Scraper

Python-скрипт для сбора данных о товарах с сайта конкурентов и экспорта результата в Excel.

## Что нужно

- Python 3.8+
- `pip`

## Установка

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Настройка

Откройте `config.json` и укажите параметры:

- `start_url` — начальная страница каталога
- `product_selector` — CSS-селектор блока товара
- `fields` — какие данные извлекаются из блока
- `next_page_selector` — кнопка или ссылка перехода на следующую страницу
- `output_file` — имя Excel-файла для результата

### Пример полей

```json
{
  "name": ".product-title@text",
  "link": ".product-title a@href",
  "price": ".product-price@text",
  "availability": ".product-stock@text"
}
```

## Запуск

```bash
python scraper.py
```

Результат сохранится в файле, указанном в `config.json`, например `competitor_prices.xlsx`.

## Структура проекта

- `scraper.py` — основной скрипт
- `config.json` — настройки селекторов и output
- `requirements.txt` — зависимости
- `.gitignore` — правила для Git

## Рекомендации

- Проверяйте CSS-селекторы на целевой странице
- Если страница загружает данные через JavaScript, классический HTML-парсер может не подойти
- Меняйте `output_file`, чтобы одним запуском не перезаписывать предыдущий результат
