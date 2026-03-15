import io
import json
import pandas as pd

from langchain_core.tools import tool


@tool
async def export_to_csv(json_data: str):
    """
        Экспортирует JSON данные в файл CSV.

        Преобразует переданные JSON данные в таблицу и сохраняет их в формате CSV.
        Возвращает файл data.csv, готовый для скачивания.

        Args:
            json_data (str): JSON-строка с данными для экспорта.
                            Ожидается массив объектов с одинаковыми ключами.
                            Пример: '[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]'

        Returns:
            dict: Словарь с полями:
                - content (str): CSV содержимое файла
                - media_type (str): "text/csv" - MIME тип для CSV
                - headers (dict): Заголовки с Content-Disposition для скачивания файла
    """
    # Очищаем JSON от возможных проблем
    json_data = json_data.strip()

    # Иногда JSON приходит с экранированными кавычками
    json_data = json_data.replace('\\"', '')

    if json_data.startswith("[") and json_data.endswith("}"):
        json_data = json_data[:-1]

    data = json.loads(json_data)

    df = pd.DataFrame(data)

    stream = io.StringIO()
    df.to_csv(stream, index=False)

    stream.seek(0)
    csv_content_full = stream.getvalue()

    csv_content = csv_content_full.encode('utf-8-sig')

    return {
        "content": csv_content,
        "media_type": "text/csv",
        "headers": {
            "Content-Disposition": "attachment; filename=data.csv"
        }
    }


@tool
async def export_to_excel(json_data: str):
    """
        Экспортирует JSON данные в файл Excel (XLSX).

        Конвертирует JSON данные в таблицу и создает файл Excel формата XLSX.
        Файл содержит один лист "Sheet1" с данными. Использует библиотеку openpyxl.

        Args:
            json_data (str): JSON-строка с данными для экспорта.
                            Должна быть массивом объектов для преобразования в таблицу.
                            Пример: '[{"product": "Laptop", "price": 1000}, {"product": "Mouse", "price": 25}]'

        Returns:
            dict: Словарь с полями:
                - content (bytes): Бинарные данные Excel файла
                - media_type (str): "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" - MIME тип для XLSX
                - headers (dict): Заголовки с Content-Disposition для скачивания файла
    """

    # Очищаем JSON от возможных проблем
    json_data = json_data.strip()

    # Иногда JSON приходит с экранированными кавычками
    json_data = json_data.replace('\\"', '')

    if json_data.startswith("[") and json_data.endswith("}"):
        json_data = json_data[:-1]

    data = json.loads(json_data)

    df = pd.DataFrame(data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

    excel_data = output.getvalue()

    return {
        "content": excel_data,
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "headers": {
            "Content-Disposition": "attachment; filename=data.xlsx"
        }
    }


@tool
async def export_to_md(json_data: str):
    """
        Экспортирует JSON данные в Markdown таблицу.

        Преобразует JSON данные в таблицу и форматирует их как Markdown-таблицу.
        Результат возвращается в виде текстового файла с расширением .md.

        Args:
            json_data (str): JSON-строка с данными для экспорта.
                            Ожидается массив объектов для создания таблицы.
                            Пример: '[{"Country": "Russia", "Capital": "Moscow"}, {"Country": "France", "Capital": "Paris"}]'

        Returns:
            dict: Словарь с полями:
                - content (str): Markdown-таблица в виде строки
                - media_type (str): "text/markdown" - MIME тип для Markdown
                - headers (dict): Заголовки с Content-Disposition для скачивания файла
    """

    # Очищаем JSON от возможных проблем
    json_data = json_data.strip()

    # Иногда JSON приходит с экранированными кавычками
    json_data = json_data.replace('\\"', '')

    if json_data.startswith("[") and json_data.endswith("}"):
        json_data = json_data[:-1]

    data = json.loads(json_data)

    df = pd.DataFrame(data)

    md_content = df.to_markdown(index=False)

    return {
        "content": md_content,
        "media_type": "text/markdown",
        "headers": {
            "Content-Disposition": "attachment; filename=data.md"
        }
    }
