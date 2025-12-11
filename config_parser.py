#!/usr/bin/env python3
"""
Преобразует входной формат в XML
"""

import re
import sys
import json
from typing import Dict, List, Any, Union, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom


class ConfigParserV21:
    """Парсер для конфигурационного языка"""

    def __init__(self):
        self.constants: Dict[str, Any] = {}
        self.result: Dict[str, Any] = {}
        self.errors: List[str] = []

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Основной метод парсинга
        Возвращает словарь с распарсенными данными
        """
        # Очищаем состояние
        self.constants.clear()
        self.result.clear()
        self.errors.clear()

        # Удаляем комментарии
        text = self._remove_comments(text)

        # Парсим построчно
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Объявление константы: name: value;
            if ':' in line and line.endswith(';'):
                self._parse_constant(line)

            # Начало словаря
            elif line.startswith('{'):
                # Собираем все до закрывающей скобки
                dict_content = line
                brace_count = dict_content.count('{') - dict_content.count('}')

                while brace_count > 0 and i + 1 < len(lines):
                    i += 1
                    dict_content += ' ' + lines[i].strip()
                    brace_count = dict_content.count('{') - dict_content.count('}')

                self._parse_dict(dict_content)

            # Присваивание (если не внутри словаря)
            elif '=' in line and not line.startswith('}'):
                self._parse_assignment(line)

            i += 1

        return self.result

    def _remove_comments(self, text: str) -> str:
        """Удаляет многострочные комментарии <# ... #>"""
        return re.sub(r'<#.*?#>', '', text, flags=re.DOTALL)

    def _parse_constant(self, line: str):
        """Парсит объявление константы: name: value;"""
        try:
            # Убираем точку с запятой
            line = line.rstrip(';')

            # Разделяем на имя и значение
            if ':' in line:
                name, value = line.split(':', 1)
                name = name.strip()
                value = value.strip()

                # Проверяем имя (только строчные буквы)
                if not re.match(r'^[a-z_]+$', name):
                    self.errors.append(f"Invalid constant name: {name}")
                    return

                # Парсим значение
                parsed_value = self._parse_value(value)
                self.constants[name] = parsed_value

        except Exception as e:
            self.errors.append(f"Error parsing constant '{line}': {e}")

    def _parse_dict(self, text: str):
        """Парсит словарь: { key = value, ... }"""
        try:
            # Находим содержимое между {}
            match = re.match(r'^\s*\{?(.*?)\}?\s*$', text, re.DOTALL)
            if not match:
                return

            content = match.group(1).strip()
            if not content:
                return

            # Разделяем пары ключ-значение
            pairs = self._split_dict_pairs(content)

            # Парсим каждую пару
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Проверяем имя ключа
                    if not re.match(r'^[a-z]+$', key):
                        self.errors.append(f"Invalid key name: {key}")
                        continue

                    # Парсим значение
                    parsed_value = self._parse_value(value)
                    self.result[key] = parsed_value

        except Exception as e:
            self.errors.append(f"Error parsing dict: {e}")

    def _split_dict_pairs(self, content: str) -> List[str]:
        """Разделяет содержимое словаря на пары ключ-значение"""
        pairs = []
        current = ""
        depth = 0  # Глубина вложенных структур

        for char in content:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                if current.strip():
                    pairs.append(current.strip())
                current = ""
                continue

            current += char

        if current.strip():
            pairs.append(current.strip())

        return pairs

    def _parse_value(self, value_str: str) -> Any:
        """Парсит значение любого типа"""
        value_str = value_str.strip()

        # Пустое значение
        if not value_str:
            return None

        # Ссылка на константу: [name]
        if value_str.startswith('[') and value_str.endswith(']'):
            const_name = value_str[1:-1].strip()
            if const_name in self.constants:
                return self.constants[const_name]
            else:
                self.errors.append(f"Undefined constant: {const_name}")
                return f"${{{const_name}}}"

        # Число
        if re.match(r'^[1-9][0-9]*$', value_str):
            return int(value_str)

        # Строка (в кавычках)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
                (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # Массив: (list ...)
        if value_str.startswith('(list'):
            return self._parse_array(value_str)

        # Словарь: { ... }
        if value_str.startswith('{'):
            # Временный парсер для вложенного словаря
            temp_parser = ConfigParserV21()
            for name, val in self.constants.items():
                temp_parser.constants[name] = val
            temp_parser._parse_dict(value_str)
            return temp_parser.result

        # Простое имя (без кавычек) - возможно строка
        if re.match(r'^[a-z]+$', value_str):
            return value_str

        return value_str

    def _parse_array(self, text: str) -> List[Any]:
        """Парсит массив: (list item1 item2 ...)"""
        try:
            # Убираем (list и )
            text = text.strip()
            if not (text.startswith('(list') and text.endswith(')')):
                return []

            # Извлекаем содержимое
            content = text[5:-1].strip()  # Убираем "(list" и ")"
            if not content:
                return []

            # Разделяем элементы (разделены пробелами)
            items = []
            current = ""
            depth = 0

            for char in content:
                if char in '{(':
                    depth += 1
                elif char in '})':
                    depth -= 1
                elif char == ' ' and depth == 0:
                    if current.strip():
                        items.append(current.strip())
                    current = ""
                    continue

                current += char

            if current.strip():
                items.append(current.strip())

            # Парсим каждый элемент
            return [self._parse_value(item) for item in items]

        except Exception as e:
            self.errors.append(f"Error parsing array: {e}")
            return []

    def _parse_assignment(self, line: str):
        """Парсит присваивание вне словаря: key = value"""
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Проверяем имя ключа
            if not re.match(r'^[a-z]+$', key):
                self.errors.append(f"Invalid key name: {key}")
                return

            # Парсим значение
            parsed_value = self._parse_value(value)
            self.result[key] = parsed_value

    def has_errors(self) -> bool:
        """Проверяет, есть ли ошибки парсинга"""
        return len(self.errors) > 0

    def get_errors(self) -> List[str]:
        """Возвращает список ошибок"""
        return self.errors


def dict_to_xml(data: Dict[str, Any], root_name: str = "config") -> str:
    """
    Конвертирует словарь в красивый XML
    """

    def _to_xml(element: ET.Element, data: Any):
        if isinstance(data, dict):
            for key, value in data.items():
                child = ET.SubElement(element, key)
                _to_xml(child, value)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(element, "item")
                _to_xml(child, item)
        elif data is not None:
            element.text = str(data)

    root = ET.Element(root_name)
    _to_xml(root, data)

    # Форматируем XML
    xml_str = ET.tostring(root, encoding='unicode')

    # Используем minidom для красивого форматирования
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="  ")

    # Убираем лишние пустые строки
    lines = pretty_xml.split('\n')
    lines = [line for line in lines if line.strip()]

    return '\n'.join(lines)


def parse_and_convert(input_text: str) -> str:
    """
    Основная функция: парсит входной текст и конвертирует в XML
    """
    parser = ConfigParserV21()
    result = parser.parse(input_text)

    if parser.has_errors():
        errors = "\n".join(parser.get_errors())
        return f"<error>\n  <message>Parsing errors found:</message>\n  <details>{errors}</details>\n</error>"

    return dict_to_xml(result)


if __name__ == "__main__":
    # Читаем из stdin
    input_text = sys.stdin.read()

    # Парсим и конвертируем
    xml_output = parse_and_convert(input_text)

    # Выводим результат
    print(xml_output)