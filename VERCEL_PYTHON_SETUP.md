# Vercel Python Runtime Setup - Complete Guide

## ✅ Структура проекта:

```
schoolcontacts/
├── api/
│   └── enrich.py          # Python serverless function (Vercel автоматически распознает)
├── frontend/               # Next.js приложение
│   ├── app/
│   │   └── api/
│   │       └── enrich/
│   │           └── route.ts  # Next.js proxy к Python функции
│   └── ...
├── models.py              # Python модели
├── main.py                # Python логика обогащения
├── search.py, scraper.py, extractor.py, validator.py
├── requirements.txt       # Python зависимости
└── vercel.json           # Vercel конфигурация
```

## 🚀 Как это работает:

1. **Frontend** → Пользователь вводит школы
2. **Next.js API Route** (`/app/api/schools/process`) → Создает job в Supabase
3. **Next.js API Route** (`/app/api/enrich`) → Вызывает Python функцию
4. **Python Function** (`/api/enrich.py`) → Обрабатывает школы через всю Python логику
5. **Supabase** → Сохраняет результаты

## 📦 Настройка Vercel:

### 1. Root Directory:
- Установите **Root Directory** = `frontend` в настройках проекта Vercel

### 2. Переменные окружения:

Добавьте ВСЕ переменные из `.env`:

```
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Keys
SERPER_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# LLM
LLM_PROVIDER=openrouter
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Validation
VALIDATE_WHATSAPP=true
VALIDATE_EMAIL=true
```

### 3. Python Dependencies:

Vercel автоматически установит зависимости из `requirements.txt` в корне проекта для Python функций.

### 4. Build Settings:

- **Framework**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (автоматически)
- **Output Directory**: `.next` (автоматически)

## 🔧 Как Vercel находит Python функции:

Vercel автоматически распознает `.py` файлы в папке `api/` в **корне проекта** (не в `frontend/`).

Файл `api/enrich.py` будет доступен как `/api/enrich` endpoint.

## ⚠️ Важные моменты:

### 1. Пути импорта:

Python функция должна правильно импортировать модули из корня проекта:
```python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### 2. Environment Variables:

Все переменные окружения должны быть установлены в Vercel Dashboard, так как Python функции не имеют доступа к `.env` файлу.

### 3. Timeout:

- **Hobby план**: 60 секунд максимум
- **Pro план**: 300 секунд

Для обработки многих школ может потребоваться разбить на батчи.

### 4. Локальная разработка:

Python функции не работают локально с `npm run dev`. Для тестирования:
- Используйте упрощенную версию (fallback)
- Или задеплойте на Vercel Preview

## 🧪 Тестирование:

1. Задеплойте на Vercel
2. Откройте приложение
3. Введите список школ
4. Проверьте логи в Vercel Dashboard → Functions → enrich
5. Проверьте результаты в Supabase

## 📊 Мониторинг:

- **Vercel Dashboard** → Functions → просмотр логов Python функций
- **Supabase Dashboard** → Table Editor → проверка данных
- **Vercel Analytics** → производительность и ошибки

## 🔄 Альтернатива (если Python функции не работают):

Если возникают проблемы с Python runtime, можно:
1. Использовать упрощенную обработку (уже реализована как fallback)
2. Задеплоить Python backend отдельно (Railway/Render)
3. Использовать Vercel Background Functions для длительных задач
