# Developer Landing API

Backend API for developer landing page with AI-powered contact form analysis and smart reply generation.

## 🚀 Как запустить проект

### Локальная установка

**Требования:**
- Python 3.13+
- Poetry (для управления зависимостями)

**Шаги:**

1. Клонируйте репозиторий и перейдите в директорию проекта:
```bash
cd developer_landing_api
```

2. Установите зависимости с помощью Poetry:
```bash
poetry install
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Настройте переменные окружения в `.env`:
```env
# Application
APP_NAME=Developer Landing API
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Mistral AI
MISTRAL_API_KEY=sk-your-api-key-here
MISTRAL_MODEL=open-mistral-nemo

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_TO=owner@example.com

# Rate Limiting
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_MAX_REQUESTS=5

# File Storage
DATA_DIR=data
LOGS_DIR=data/logs
```

5. Запустите сервер:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker

**С помощью Docker Compose:**
```bash
docker-compose up --build
```

**Вручную:**
```bash
docker build -t developer-landing-api .
docker run -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data developer-landing-api
```

### Heroku

Проект готов к развертыванию на Heroku. Используйте `Procfile` и `runtime.txt` для автоматического развертывания.

## 🛠 Стек технологий

### Backend
- **Язык**: Python 3.13
- **Фреймворк**: FastAPI 0.139.2
- **ASGI Server**: Uvicorn 0.51.0
- **Валидация данных**: Pydantic 2.13.4
- **Настройки**: Pydantic Settings 2.14.2
- **Логирование**: Loguru 0.7.3

### AI
- **Mistral AI 2.7.1** - для анализа контактных форм, генерации умных ответов и классификации срочности
- **Tenacity 9.1.4** - для retry-логики при вызовах AI API

### Email
- **aiosmtplib 5.1.2** - асинхронная отправка email через SMTP
- **python-multipart 0.0.32** - для обработки multipart данных

### Утилиты
- **python-dotenv 1.2.2** - загрузка переменных окружения
- **aiofiles 25.1.0** - асинхронная работа с файлами
- **psutil 7.2.2** - системная информация для health checks
- **httpx 0.28.1** - асинхронный HTTP клиент

## 🏗 Архитектура

### Структура проекта

```
developer_landing_api/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── contact.py      # Эндпоинт контактной формы
│   │       ├── health.py       # Health check endpoint
│   │       └── metrics.py      # Метрики и статистика
│   ├── middleware/
│   │   ├── error_handler.py    # Глобальная обработка ошибок
│   │   └── logging.py          # Логирование запросов
│   ├── models/
│   │   └── contact.py          # Pydantic модели
│   ├── services/
│   │   ├── ai_service.py       # Mistral AI интеграция
│   │   ├── contact_service.py  # Бизнес-логика контактов
│   │   ├── email_service.py    # Email отправка
│   │   └── rate_limiter.py     # Rate limiting
│   ├── utils/
│   │   └── file_storage.py     # Файловое хранилище
│   ├── config.py               # Конфигурация приложения
│   └── main.py                 # Точка входа FastAPI
├── data/
│   ├── logs/                   # Логи приложения
│   ├── metrics.json            # Статистика и метрики
│   └── rate_limits.json        # Rate limiting данные
├── .env.example                # Пример переменных окружения
├── dockerfile                  # Docker конфигурация
├── docker-compose.yml          # Docker Compose конфигурация
├── pyproject.toml              # Python зависимости
└── runtime.txt                 # Python версия для Heroku
```

### Паттерны проектирования

1. **Clean Architecture** - четкое разделение на слои (api, services, models, utils)
2. **Dependency Injection** - использование FastAPI Depends для внедрения зависимостей
3. **Service Layer Pattern** - бизнес-логика в сервисах, отделенная от API routes
4. **Repository Pattern** - FileStorage как абстракция над файловым хранилищем
5. **Middleware Pattern** - логирование и обработка ошибок через middleware
6. **Factory Pattern** - создание сервисов в маршрутах
7. **Strategy Pattern** - fallback логика в AI сервисе

### Обоснование выбора технологий

- **FastAPI**: Высокая производительность, автоматическая документация, встроенная валидация
- **Mistral AI**: Доступный и мощный AI API с поддержкой JSON mode, хорошая цена/качество
- **Файловое хранилище**: Простота развертывания, отсутствие необходимости в базе данных для MVP
- **Loguru**: Удобное логирование с ротацией файлов и красивым выводом
- **Poetry**: Надежное управление зависимостями и виртуальными окружениями

## 📡 Реализация API

### Эндпоинты

#### POST /api/contact
Отправка контактной формы с AI анализом.

**Request Body:**
```json
{
  "name": "John Doe",
  "phone": "+1234567890",
  "email": "john@example.com",
  "comment": "I need a website for my business"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Thank you for your inquiry. We will contact you soon!",
  "data": {
    "name": "John Doe",
    "phone": "+1234567890",
    "email": "john@example.com",
    "comment": "I need a website for my business"
  },
  "ai_analysis": {
    "sentiment": "positive",
    "priority": "high",
    "category": "web_development",
    "auto_reply_suggestion": "Thank you for reaching out about your web development project...",
    "smart_reply": "Dear John, thank you for your interest in web development services...",
    "urgency_info": {
      "urgency": "medium",
      "response_time": "24 hours",
      "reason": "Standard business inquiry"
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Response (429 Too Many Requests):**
```json
{
  "detail": {
    "message": "Too many requests. Please try again later.",
    "retry_after": 1800,
    "limit": 5
  }
}
```

#### GET /api/health
Health check с системной информацией.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Developer Landing API",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "environment": "development",
  "system": {
    "cpu_usage": "15.5%",
    "memory_usage": "45.2%",
    "disk_usage": "60.1%",
    "python_version": "3.13.0"
  },
  "checks": {
    "mistral_configured": true,
    "smtp_configured": true,
    "data_directory_writable": true
  }
}
```

#### GET /api/metrics
Получение метрик и статистики.

**Response (200 OK):**
```json
{
  "total_requests": 150,
  "successful_submissions": 145,
  "failed_submissions": 5,
  "daily_stats": {
    "2024-01-15": 25,
    "2024-01-14": 30
  },
  "sentiment_distribution": {
    "positive": 80,
    "neutral": 60,
    "negative": 10
  },
  "category_distribution": {
    "web_development": 50,
    "consulting": 30,
    "general": 20
  },
  "system": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "uptime": "see health endpoint for uptime"
  }
}
```

#### GET /
Корневой эндпоинт с информацией о сервисе.

**Response (200 OK):**
```json
{
  "service": "Developer Landing API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/health"
}
```

### Валидация и обработка ошибок

**Валидация данных:**
- Имя: 2-100 символов, только буквы, пробелы и дефисы
- Телефон: 10-20 цифр, автоматическое форматирование в международный формат
- Email: валидация через Pydantic EmailStr
- Комментарий: опционально, максимум 1000 символов

**Обработка ошибок:**
- Глобальный exception handler для всех необработанных исключений
- Детальное логирование ошибок с контекстом
- Fallback режим при недоступности AI сервисов
- Graceful degradation при ошибках rate limiting

## 🤖 AI-интеграция

### Используемые AI инструменты

**Mistral AI** используется для трех задач:

1. **Анализ контактных форм** - определение тональности, приоритета и категории запроса
2. **Генерация умных ответов** - создание персонализированных ответов клиентам
3. **Классификация срочности** - определение уровня срочности и рекомендуемого времени ответа

### Реализация fallback

При недоступности Mistral AI или ошибках API:

1. **Анализ контактов**: Возвращает дефолтный анализ (sentiment: neutral, priority: medium, category: general)
2. **Умные ответы**: Использует шаблонный ответ с именем клиента
3. **Классификация срочности**: Возвращает medium срочность с 24-часовым временем ответа

**Retry логика:**
- 3 попытки с экспоненциальной задержкой (2-10 секунд)
- Логирование каждой попытки
- Автоматический fallback после исчерпания попыток

### Промпты

**Промпт для анализа контактов:**
```
You are an AI assistant that analyzes client inquiries for a software developer's landing page.
Analyze each inquiry and provide structured JSON output.

Categories can be:
- web_development: Website/web app development requests
- mobile_development: Mobile app development requests
- consulting: Technical consulting or advice
- job_opportunity: Job offers or career opportunities
- partnership: Business partnerships or collaborations
- support: Technical support requests
- general: General inquiries

Always respond with valid JSON only, no markdown formatting.
```

**Промпт для генерации ответов:**
```
You are a professional software developer responding to client inquiries.
Write personalized, professional responses that:
1. Address the client by name
2. Reference their specific inquiry
3. Set clear expectations about next steps
4. Maintain a friendly but professional tone
5. Are concise (2-3 sentences)
```

**Промпт для классификации срочности:**
```
You are an AI assistant that classifies the urgency of client inquiries.

Classify the urgency of this inquiry and return JSON with:
- urgency: "low", "medium", "high", or "critical"
- response_time: suggested response time (e.g., "24 hours", "4 hours", "1 hour")
- reason: brief explanation

Respond ONLY with valid JSON.
```

## ✨ Что сделано с помощью AI

### Сгенерированные части кода

1. **AIService (ai_service.py)** - полностью сгенерирован с помощью AI:
   - Интеграция с Mistral AI API
   - Retry логика с tenacity
   - JSON парсинг и извлечение
   - Fallback механизмы

2. **EmailService (email_service.py)** - HTML шаблоны email сгенерированы AI:
   - HTML для notification email
   - HTML для confirmation email
   - Стилизация и верстка

3. **RateLimiter (rate_limiter.py)** - логика rate limiting сгенерирована AI:
   - Sliding window алгоритм
   - Асинхронная работа с файлами
   - Очистка устаревших записей

4. **FileStorage (file_storage.py)** - сгенерирован AI:
   - Структура метрик
   - Асинхронное сохранение/загрузка JSON
   - Обновление статистики

### Ручные исправления

1. **Конфигурация**: Добавлена проверка доступности Mistral API через settings
2. **Логирование**: Улучшено логирование во всех сервисах для отладки
3. **Валидация**: Добавлена кастомная валидация телефона и имени в Pydantic моделях
4. **Middleware**: Добавлен middleware для логирования запросов
5. **Error handling**: Улучшена глобальная обработка ошибок
6. **CORS**: Настройка CORS для фронтенда интеграции
7. **Health check**: Добавлена проверка системных ресурсов

## 💾 Хранение данных

### Хранение логов

**Логирование реализовано через Loguru:**
- Логи сохраняются в директории `data/logs/`
- Автоматическая ротация файлов по размеру и времени
- Разные уровни логирования (DEBUG, INFO, WARNING, ERROR)
- Структурированные логи с контекстом

**Пример структуры логов:**
```
data/logs/
├── app_2024-01-15.log
├── app_2024-01-14.log
└── app_2024-01-13.log
```

### Rate limiting

**Реализация:**
- Хранение в JSON файле `data/rate_limits.json`
- Sliding window алгоритм
- Идентификация клиента по IP адресу (с поддержкой X-Forwarded-For)
- Автоматическая очистка устаревших записей

**Структура данных:**
```json
{
  "192.168.1.1": {
    "window_start": 1705300800,
    "count": 3
  },
  "192.168.1.2": {
    "window_start": 1705300900,
    "count": 1
  }
}
```

**Настройки:**
- `RATE_LIMIT_WINDOW`: 3600 секунд (1 час)
- `RATE_LIMIT_MAX_REQUESTS`: 5 запросов на окно

### Хранение статистики

**Метрики сохраняются в `data/metrics.json`:**

```json
{
  "total_requests": 150,
  "successful_submissions": 145,
  "failed_submissions": 5,
  "daily_stats": {
    "2024-01-15": 25,
    "2024-01-14": 30
  },
  "sentiment_distribution": {
    "positive": 80,
    "neutral": 60,
    "negative": 10
  },
  "category_distribution": {
    "web_development": 50,
    "consulting": 30,
    "general": 20
  },
  "last_updated": "2024-01-15T10:30:00.000Z"
}
```

**Обновление метрик:**
- Инкремент общего счетчика запросов
- Разделение на успешные и неуспешные
- Распределение по тональности (sentiment)
- Распределение по категориям
- Ежедневная статистика

## 📝 Дополнительная информация

### API Documentation

Автоматическая документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Мониторинг

- **Health Check**: `/api/health` - проверка состояния сервиса
- **Metrics**: `/api/metrics` - статистика использования
- **Logs**: `data/logs/` - файлы логов

### Безопасность

- Rate limiting для защиты от спама
- Валидация всех входных данных
- CORS настройка для фронтенда
- Скрытие чувствительных данных в логах
- Environment variables для секретов

## 👤 Автор

Sladkiy-bubalex - shadow.ru_93@mail.ru
