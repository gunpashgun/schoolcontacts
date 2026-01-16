# Vercel Python Runtime Setup

## Структура для Python Serverless Functions

Vercel автоматически распознает Python файлы в папке `api/` как serverless functions.

## Файловая структура:

```
schoolcontacts/
├── api/
│   └── enrich.py          # Python serverless function
├── frontend/
│   └── app/
│       └── api/
│           └── enrich/
│               └── route.ts  # Next.js proxy to Python function
└── vercel.json            # Vercel configuration
```

## Как это работает:

1. **Next.js API Route** (`/app/api/enrich/route.ts`):
   - Принимает запрос от frontend
   - Вызывает Python serverless function

2. **Python Function** (`/api/enrich.py`):
   - Использует всю существующую Python логику
   - Обрабатывает школы через `LeadEnrichmentEngine`
   - Сохраняет результаты в Supabase

## Настройка Vercel:

### 1. Переменные окружения:

Добавьте в Vercel все переменные из `.env`:
- `SERPER_API_KEY`
- `OPENROUTER_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY` (Service Role Key)
- И другие...

### 2. Python Runtime:

Vercel автоматически определит Python функции по расширению `.py` в папке `api/`.

### 3. Dependencies:

Vercel автоматически установит зависимости из `requirements.txt` в корне проекта.

## Ограничения Vercel Python:

- **Timeout**: Максимум 60 секунд для Hobby плана, 300 секунд для Pro
- **Memory**: Ограниченная память
- **Cold Start**: Первый запрос может быть медленным

## Рекомендации:

1. **Для больших батчей**: Обрабатывайте школы по частям (по 5-10 за раз)
2. **Для длительной обработки**: Используйте фоновые задачи или очереди
3. **Мониторинг**: Следите за логами в Vercel Dashboard

## Альтернатива (если Python функции не работают):

Можно использовать **Vercel Cron Jobs** для периодической обработки или **Vercel Background Functions** для длительных задач.

