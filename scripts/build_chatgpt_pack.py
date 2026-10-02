#!/usr/bin/env python3
"""Build a small allowlisted distribution, never package private working data."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INTRO = '''Alpes Researcher | Экспорт PDF и Word | Версия 1.0

Для ChatGPT/агента, не для выполнения пользователем.
При доступном Python сохрани код ниже как export_report.py во временной папке.
Подготовь report.json из проверенного исследования и вызови export(data, output, font=None).
Должны быть доступны reportlab, python-docx и TTF с кириллицей. Без этих возможностей
используй штатные инструменты документов или объясни ограничение. Не обещай выполнение,
если инструмента нет. Не скачивай и не отправляй пользовательские данные в сторонние сервисы.

КОНТРАКТ JSON
{
 "title": "Название исследования", "date": "YYYY-MM-DD",
 "objective": "Рабочий вопрос", "identity": "Компания и проверенное юрлицо либо неизвестно",
 "summary": [{"kind": "gap", "text": "Ключевой пробел", "sources": []}],
 "sections": [{"title": "Раздел", "items": [{"kind": "action", "text": "Следующий шаг", "sources": []}]}],
 "sources": [{"id": "S01", "title": "Заголовок источника", "url": "https://example.org/",
 "locator": "Для вложения — имя и страница вместо URL", "checked_at": "YYYY-MM-DD",
 "status": "checked", "entity": "Объект", "period": "Период данных",
 "published_at": "Дата публикации либо неизвестно", "note": "Ограничение/краткая выдержка"}]
}
Это схема, не готовые данные; даты и поля нужно заполнить реально проверенными значениями.
kind: fact, claim, hypothesis, gap, action. fact/claim требуют sources с существующими ID.
У hypothesis обязательны alternative (альтернативное объяснение) и question (проверочный вопрос).
status источника: checked, claim, partial, unavailable, not_checked, user_material.
Для fact ссылки должны иметь status checked или user_material; материал пользователя
нужно явно атрибутировать в тексте, он не считается независимой проверкой.
Нет источников — пустой sources и только gap/action/hypothesis, без выдуманных фактов.
Каждый раздел имеет непустой items. Содержание не должно содержать внутренние токены цитирования.
Не включай весь личный профиль в пересылаемый отчёт. Все строки — обычный текст, без HTML-разметки.
После выполнения проверь три файла, извлечение кириллицы, ссылки и страницы.
Экспортёр проверяет структуру, а не истинность фактов. Пример JSON не является исследованием.

BEGIN PYTHON
'''


def generated():
    return INTRO + (ROOT/'scripts/export_report.py').read_text(encoding='utf-8') + '\nEND PYTHON\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = ROOT/'chatgpt/04_EXPORTER.txt'
    expected = generated()
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != expected:
            parser.exit(1, '04_EXPORTER.txt устарел: запустите сборку\n')
        print('Export knowledge file is current')
        return
    target.write_text(expected, encoding='utf-8')
    names = ['docs/START_HERE.txt','LICENSE','ATTRIBUTION.md'] + [f'chatgpt/{name}' for name in (
        '00_PROJECT_INSTRUCTIONS.txt','01_ONBOARDING.txt','02_RESEARCH.txt','03_DELIVERABLES.txt','04_EXPORTER.txt')]
    dist = ROOT/'dist'; dist.mkdir(exist_ok=True)
    path = dist/'Alpes-ChatGPT-Starter.zip'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(ROOT/name, 'START_HERE.txt' if name == 'docs/START_HERE.txt' else name)
    print(path)


if __name__ == '__main__':
    main()
