# Конфигурационный парсер (Вариант №21)

**Дисциплина:** Конфигурационное управление  
**Группа:** ИКБО-21-24

---

## Описание проекта

Инструмент командной строки для преобразования конфигурационных файлов из учебного конфигурационного языка в XML формат. Парсер разработан с нуля без использования сторонних библиотек для синтаксического анализа.

### Основные возможности

- **Парсинг учебного конфигурационного языка** - полная поддержка синтаксиса варианта №21
- **Преобразование в XML** - корректная конвертация всех конструкций языка
- **Обработка ошибок** - детальные сообщения о синтаксических ошибках
- **Константные выражения** - вычисление выражений на этапе трансляции
- **Тестовое покрытие** - комплексные тесты всех возможностей языка

---

## Старт программы

### Запуск конвертации

```bash
# Из файла в консоль
python cli.py examples/web_server.conf

# Из stdin
python cli.py < examples/database.conf

# С выводом в файл
python cli.py examples/app_config.conf -o output.xml

# Только проверка синтаксиса
python cli.py --validate examples/web_server.conf
```

### Запуск теста

```bash
# Все тесты
pytest tests/ -v

# Конкретный тестовый класс
python -m pytest tests/test_parser.py::TestConfigParserV21 -v

# С покрытием кода
python -m pytest tests/ --cov=config_parser --cov-report=html
```

#### Пример тестового файла
#### Входной файл (app_config.conf)

```python
<# Конфигурация приложения #>
app_version: 2;
debug_mode: false;

{
    application = {
        name = "MyApp",
        version = [app_version],
        debug = [debug_mode],
        features = (list authentication api websocket caching),
        limits = {
            max_requests = 1000,
            memory = "512MB"
        }
    }
}
```

#### Тестовый код

```python
def test_complex_application_config(self):
    """Тест комплексной конфигурации приложения"""
    input_text = '''
    version: 2;
    debug: false;
    
    {
        application = {
            name = "MyApplication",
            version = [version],
            debug = [debug],
            server = {
                host = "127.0.0.1",
                port = 8080,
                ssl = true
            },
            features = (list auth api logging),
            limits = {
                timeout = 30,
                memory = "512MB"
            }
        }
    }
    '''
    
    result = self.parser.parse(input_text)
    
    # Проверка констант
    assert self.parser.constants['version'] == 2
    assert self.parser.constants['debug'] == False
    
    # Проверка структуры
    assert 'application' in result
    app = result['application']
    
    assert app['name'] == "MyApplication"
    assert app['version'] == 2  # Из константы
    assert app['debug'] == False  # Из константы
    
    # Проверка вложенного словаря
    assert 'server' in app
    assert app['server']['host'] == "127.0.0.1"
    assert app['server']['port'] == 8080
    assert app['server']['ssl'] == True
    
    # Проверка массива
    assert 'features' in app
    assert isinstance(app['features'], list)
    assert 'auth' in app['features']
    assert 'api' in app['features']
    assert 'logging' in app['features']
    
    # Проверка типов данных
    assert isinstance(app['server']['port'], int)
    assert isinstance(app['server']['ssl'], bool)
    assert isinstance(app['debug'], bool)
```

#### Ожидаемый XML

```XML
<?xml version="1.0" ?>
<config>
  <application>
    <name>MyApplication</name>
    <version>2</version>
    <debug>false</debug>
    <server>
      <host>127.0.0.1</host>
      <port>8080</port>
      <ssl>true</ssl>
    </server>
    <features>
      <item>auth</item>
      <item>api</item>
      <item>logging</item>
    </features>
    <limits>
      <timeout>30</timeout>
      <memory>512MB</memory>
    </limits>
  </application>
</config>
```

### Структура проекта

```
config4/
├── config_parser.py          # Основной парсер (лексический + синтаксический анализ)
├── cli.py                    # Главный исполняемый файл (CLI интерфейс)
├── README.md                 # Документация проекта (этот файл)
├── requirements.txt          # Зависимости проекта (pytest для тестирования)
│
├── tests/                    # Тесты
│   └── test_parser.py       # Тесты примеров конфигураций
│
├── examples/                 # Примеры конфигураций
│   ├── web_server.conf      # Пример 1: Конфигурация веб-сервера
│   ├── database.conf        # Пример 2: Конфигурация базы данных
│   └── app_config.conf      # Пример 3: Конфигурация приложения
│
└── output.xml               # Пример выходного XML файла
```
