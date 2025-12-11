#!/usr/bin/env python3
"""
Тесты для парсера конфигурационного языка (вариант 21)
"""

import sys
import os
import pytest
from io import StringIO

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_parser import ConfigParserV21, dict_to_xml, parse_and_convert


class TestConfigParserV21:
    """Тесты основного парсера"""

    def setup_method(self):
        self.parser = ConfigParserV21()

    def test_simple_dict(self):
        """Тест простого словаря"""
        input_text = '''{
            port = 8080,
            host = "localhost"
        }'''

        result = self.parser.parse(input_text)

        assert 'port' in result
        assert 'host' in result
        assert result['port'] == 8080
        assert result['host'] == 'localhost'
        assert not self.parser.has_errors()

    def test_constants(self):
        """Тест объявления и использования констант"""
        input_text = '''version: 2;
        settings = (list 1 2 [version])'''

        result = self.parser.parse(input_text)

        # Проверяем константу
        assert self.parser.constants.get('version') == 2

        # Проверяем массив с использованием константы
        assert 'settings' in result
        assert isinstance(result['settings'], list)
        assert 2 in result['settings']

    def test_nested_dict(self):
        """Тест вложенного словаря"""
        input_text = '''{
            database = {
                name = "test",
                tables = (list users products)
            }
        }'''

        result = self.parser.parse(input_text)

        assert 'database' in result
        assert isinstance(result['database'], dict)
        assert result['database']['name'] == 'test'
        assert 'tables' in result['database']
        assert isinstance(result['database']['tables'], list)
        assert 'users' in result['database']['tables']
        assert 'products' in result['database']['tables']

    def test_array(self):
        """Тест массива"""
        input_text = '''features = (list api auth logging)'''

        result = self.parser.parse(input_text)

        assert 'features' in result
        assert isinstance(result['features'], list)
        assert len(result['features']) == 3
        assert 'api' in result['features']
        assert 'auth' in result['features']
        assert 'logging' in result['features']

    def test_comments(self):
        """Тест удаления комментариев"""
        input_text = '''<# Это комментарий #>
        {
            <# Еще комментарий #>
            port = 8080,
            host = "localhost"
        }'''

        result = self.parser.parse(input_text)

        # Комментарии должны быть удалены
        assert 'port' in result
        assert 'host' in result
        assert result['port'] == 8080
        assert result['host'] == 'localhost'

    def test_error_undefined_constant(self):
        """Тест ошибки неопределенной константы"""
        input_text = '''value = [undefined_const]'''

        result = self.parser.parse(input_text)

        # Должна быть ошибка
        assert self.parser.has_errors()
        assert any('undefined' in err.lower() for err in self.parser.get_errors())

    def test_invalid_key_name(self):
        """Тест неверного имени ключа"""
        input_text = '''{ Port = 8080 }'''  # С большой буквы

        result = self.parser.parse(input_text)

        # Должна быть ошибка
        assert self.parser.has_errors()

    def test_complex_structure(self):
        """Тест сложной структуры"""
        input_text = '''max_connections: 100;
        {
            server = {
                port = 8080,
                workers = 4,
                limits = {
                    connections = [max_connections],
                    timeout = 30
                },
                modules = (list auth cache database)
            }
        }'''

        result = self.parser.parse(input_text)

        # Проверяем константу
        assert self.parser.constants['max_connections'] == 100

        # Проверяем структуру
        assert 'server' in result
        server = result['server']

        assert server['port'] == 8080
        assert server['workers'] == 4

        # Проверяем вложенный словарь
        assert 'limits' in server
        assert server['limits']['connections'] == 100  # Из константы
        assert server['limits']['timeout'] == 30

        # Проверяем массив
        assert 'modules' in server
        assert isinstance(server['modules'], list)
        assert len(server['modules']) == 3


class TestXMLConverter:
    """Тесты конвертации в XML"""

    def test_dict_to_xml_simple(self):
        """Тест простой конвертации в XML"""
        data = {
            'server': {
                'port': 8080,
                'host': 'localhost'
            }
        }

        xml_output = dict_to_xml(data)

        # Проверяем ключевые элементы
        assert '<server>' in xml_output
        assert '<port>8080</port>' in xml_output
        assert '<host>localhost</host>' in xml_output
        assert xml_output.startswith('<?xml')

    def test_dict_to_xml_with_list(self):
        """Тест конвертации с массивом"""
        data = {
            'features': ['api', 'auth', 'database']
        }

        xml_output = dict_to_xml(data)

        assert '<features>' in xml_output
        assert '<item>api</item>' in xml_output
        assert '<item>auth</item>' in xml_output
        assert '<item>database</item>' in xml_output

    def test_empty_dict(self):
        """Тест пустого словаря"""
        data = {}

        xml_output = dict_to_xml(data)

        # Допускаем обе формы: <config></config> или <config/>
        assert 'config' in xml_output
        assert xml_output.strip().endswith('>')


class TestIntegration:
    """Интеграционные тесты"""

    def test_full_pipeline(self):
        """Тест полного пайплайна: парсинг -> XML"""
        input_text = '''{
            application = {
                name = "TestApp",
                version = 1,
                modules = (list web api database)
            }
        }'''

        xml_output = parse_and_convert(input_text)

        # Проверяем что получился валидный XML
        assert '<application>' in xml_output
        assert '<name>TestApp</name>' in xml_output
        assert '<version>1</version>' in xml_output
        assert '<modules>' in xml_output
        assert '<item>web</item>' in xml_output

    def test_error_handling(self):
        """Тест обработки ошибок"""
        input_text = '''{ invalid_key_name = value }'''

        xml_output = parse_and_convert(input_text)

        # Должен вернуться XML с ошибкой
        assert '<error>' in xml_output
        assert 'Invalid key name' in xml_output


def test_command_line_interface():
    """Тест интерфейса командной строки"""
    # Этот тест можно расширить для тестирования cli.py
    pass


if __name__ == "__main__":
    # Запуск тестов вручную
    pytest.main([__file__, '-v'])