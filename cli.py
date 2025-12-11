#!/usr/bin/env python3
"""
Интерфейс командной строки для парсера конфигураций
"""

import sys
import argparse
from config_parser import parse_and_convert


def main():
    parser = argparse.ArgumentParser(
        description='Конвертер конфигурационного языка (вариант 21) в XML',
        epilog='Пример: python cli.py < config.conf'
    )

    parser.add_argument(
        'file',
        nargs='?',
        type=argparse.FileType('r', encoding='utf-8'),
        default=sys.stdin,
        help='Входной файл (если не указан, читает из stdin)'
    )

    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w', encoding='utf-8'),
        default=sys.stdout,
        help='Выходной файл (по умолчанию stdout)'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Только проверить синтаксис'
    )

    args = parser.parse_args()

    try:
        # Читаем входные данные
        input_text = args.file.read()

        if not input_text.strip():
            print("Ошибка: входные данные пусты", file=sys.stderr)
            sys.exit(1)

        # Парсим и конвертируем
        xml_output = parse_and_convert(input_text)

        if args.validate:
            if "<error>" in xml_output:
                print("Синтаксические ошибки найдены!", file=sys.stderr)
                print(xml_output, file=sys.stderr)
                sys.exit(1)
            else:
                print("Синтаксис корректен", file=sys.stderr)
                sys.exit(0)

        # Записываем результат
        args.output.write(xml_output)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()