# Price List Cleaner

Утилита для очистки и нормализации прайс-листов в формате CSV или Excel.

## Что делает

- удаляет пустые строки
- убирает дубликаты
- приводит цены к числовому формату
- пересчитывает стоимость по наценке
- унифицирует названия товаров
- выгружает чистый прайс-лист в CSV/Excel

## Установка

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Запуск

```bash
python process_price_list.py input.xlsx output.csv --markup 10
```

### Примеры

- Обработать `input.xlsx` и сохранить результат в `output.csv`:
  ```bash
  python process_price_list.py input.xlsx output.csv --markup 10
  ```
- Обработать CSV и сохранить в Excel:
  ```bash
  python process_price_list.py input.csv output.xlsx --markup 15
  ```

## Параметры

- `input` — входной файл `.csv` или `.xlsx`
- `output` — выходной файл `.csv` или `.xlsx`
- `--sheet` — имя листа Excel
- `--delimiter` — разделитель для CSV (по умолчанию `,`)
- `--price-cols` — список колонок с ценами
- `--name-col` — колонка с названием товара
- `--markup` — процент наценки
- `--rename-map` — JSON-строка или путь к файлу с переименованиями `old:new`
- `--drop-cols` — колонки для удаления
- `--keep-cols` — колонки для сохранения

## Структура проекта

- `process_price_list.py` — основной скрипт обработки
- `requirements.txt` — зависимости
- `.gitignore` — исключения для Git

## Примечания

- Если обработка не проходит, проверьте заголовки колонок в таблице
- Используйте `--rename-map` для приведения названий к единому виду
- Для Excel-файла укажите `--sheet`, если лист не называется `Sheet1`
