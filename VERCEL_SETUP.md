# Vercel Deployment - Complete Setup

## ✅ Что уже готово:

1. ✅ SQL схема выполнена в Supabase
2. ✅ Next.js API routes созданы (Vercel Serverless Functions)
3. ✅ Frontend компоненты готовы
4. ✅ Supabase интеграция настроена

## 🚀 Деплой на Vercel:

### Шаг 1: Подключить репозиторий

1. Зайдите на https://vercel.com
2. Нажмите **Add New Project**
3. Импортируйте: `gunpashgun/schoolcontacts`
4. **Важно:** Установите **Root Directory** = `frontend`

### Шаг 2: Переменные окружения

В настройках проекта → **Environment Variables** добавьте:

```
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6Y2R6eXFoYWRjenhzdnZmZGhnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODU4MzI0OCwiZXhwIjoyMDg0MTU5MjQ4fQ.9sLSEf4IdGz9rGLJe8eTxOFLG5vCsB2tL_XximDVDUk
```

**Важно:** `SUPABASE_SERVICE_ROLE_KEY` нужен для server-side API routes.

### Шаг 3: Настройки Build

- **Framework Preset**: Next.js (автоматически)
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (по умолчанию)
- **Output Directory**: `.next` (по умолчанию)

### Шаг 4: Деплой

1. Нажмите **Deploy**
2. Дождитесь завершения билда
3. Получите URL: `https://your-project.vercel.app`

## 📝 Как это работает:

### Архитектура:

```
Frontend (Next.js) → API Routes (Vercel Serverless) → Supabase
```

- **Frontend**: React компоненты, формы, таблицы
- **API Routes**: `/app/api/*` - обработка запросов
- **Supabase**: Хранение данных (jobs, results, leads)

### Обработка школ:

1. Пользователь вводит список школ
2. API route `/api/schools/process` создает job в Supabase
3. Запускается фоновая обработка (упрощенная версия)
4. Результаты сохраняются в Supabase
5. Frontend показывает прогресс и результаты

## ⚠️ Важно:

### Текущая реализация:

Сейчас обработка школ использует **упрощенную версию** (создает placeholder результаты).

Для **полноценной обработки** с Python логикой есть варианты:

1. **Вариант A**: Задеплоить Python backend отдельно (Railway/Render)
   - Добавить `PYTHON_API_URL` в переменные окружения
   - API routes будут вызывать Python backend

2. **Вариант B**: Использовать Vercel Python runtime
   - Создать Python serverless functions
   - Более сложная настройка

3. **Вариант C**: Использовать очередь (BullMQ + Redis)
   - Для асинхронной обработки
   - Требует дополнительных сервисов

### Рекомендация:

Для начала используйте текущую упрощенную версию для тестирования UI и интеграции с Supabase. Затем можно добавить полноценную обработку через отдельный Python backend.

## 🧪 Тестирование:

1. Откройте задеплоенное приложение
2. Введите список школ в формате:
```
PPPK Petra - Private Christian (Elementary to High School)
Yohanes Gabriel Foundation - Private Catholic (Elementary to High School)
```
3. Нажмите "Process Schools"
4. Дождитесь завершения
5. Просмотрите результаты и скачайте их

## 🔧 Troubleshooting:

### Ошибка: "Supabase connection failed"
- Проверьте переменные окружения в Vercel
- Убедитесь, что `SUPABASE_SERVICE_ROLE_KEY` установлен

### Ошибка: "Job not found"
- Проверьте, что SQL схема выполнена в Supabase
- Убедитесь, что таблицы `jobs`, `school_results`, `person_leads` существуют

### Build fails
- Проверьте Root Directory = `frontend`
- Убедитесь, что все зависимости в `package.json`

