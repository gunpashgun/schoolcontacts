# 🚀 Quick Deploy Guide

## Шаг 1: Подключить репозиторий в Vercel

1. Зайдите на https://vercel.com
2. **Add New Project** → Импортируйте `AlgonovaTech/schoolcontacts`
3. **Root Directory**: `frontend` ⚠️ ВАЖНО!
4. **Framework Preset**: Next.js (автоматически)

## Шаг 2: Переменные окружения

В **Settings → Environment Variables** добавьте:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6Y2R6eXFoYWRjenhzdnZmZGhnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODU4MzI0OCwiZXhwIjoyMDg0MTU5MjQ4fQ.9sLSEf4IdGz9rGLJe8eTxOFLG5vCsB2tL_XximDVDUk

# Остальные настройки (API ключи, LLM, валидация) захардкожены в config.py
# При необходимости можно переопределить через переменные окружения
```

## Шаг 3: Деплой

Нажмите **Deploy** и дождитесь завершения.

## Шаг 4: Проверка

1. Откройте задеплоенное приложение
2. Введите тестовый список школ:
```
PPPK Petra - Private Christian (Elementary to High School)
Yohanes Gabriel Foundation - Private Catholic (Elementary to High School)
```
3. Нажмите "Process Schools"
4. Проверьте результаты

## 📝 Структура:

- **Frontend**: Next.js в `frontend/`
- **Python Functions**: В `api/enrich.py` (Vercel автоматически распознает)
- **Database**: Supabase

## ⚠️ Важно:

- **Root Directory** должен быть `frontend`
- Python функции находятся в корне проекта (`api/`), не в `frontend/`
- Все переменные окружения должны быть установлены в Vercel

## 🔍 Troubleshooting:

### Python функция не работает:
- Проверьте логи в Vercel Dashboard → Functions
- Убедитесь, что все переменные окружения установлены
- Проверьте, что `requirements.txt` в корне проекта

### Ошибки импорта:
- Убедитесь, что все Python файлы в корне проекта
- Проверьте пути в `api/enrich.py`

## 📚 Подробная документация:

- `VERCEL_PYTHON_SETUP.md` - Детальная настройка Python runtime
- `VERCEL_SETUP.md` - Общая настройка Vercel
- `SUPABASE_SETUP.md` - Настройка базы данных

