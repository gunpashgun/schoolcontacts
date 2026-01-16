# Vercel Deployment Guide

## Шаг 1: Подключить репозиторий к Vercel

1. Зайдите на https://vercel.com
2. Нажмите **Add New Project**
3. Импортируйте репозиторий: `gunpashgun/schoolcontacts`
4. Выберите **Root Directory**: `frontend`

## Шаг 2: Настроить переменные окружения

В настройках проекта Vercel добавьте следующие переменные:

### Обязательные:
```
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
```

### API URL (после деплоя backend):
```
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

**Важно:** Для локальной разработки используйте `http://localhost:8000`, но для продакшена нужен реальный URL вашего FastAPI backend.

## Шаг 3: Настройки Build

- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (по умолчанию)
- **Output Directory**: `.next` (по умолчанию)
- **Install Command**: `npm install` (по умолчанию)

## Шаг 4: Деплой

1. Нажмите **Deploy**
2. Дождитесь завершения билда
3. Получите URL вашего приложения (например: `https://schoolcontacts.vercel.app`)

## Шаг 5: Настроить Backend API URL

После деплоя backend (Railway/Render/Fly.io):

1. Зайдите в настройки проекта Vercel
2. Перейдите в **Environment Variables**
3. Обновите `NEXT_PUBLIC_API_URL` на URL вашего backend
4. Передеплойте проект

## Troubleshooting

### Ошибка: "API request failed"
- Проверьте, что `NEXT_PUBLIC_API_URL` правильно настроен
- Убедитесь, что backend доступен и CORS настроен

### Ошибка: "Supabase connection failed"
- Проверьте `NEXT_PUBLIC_SUPABASE_URL` и `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Убедитесь, что RLS policies настроены в Supabase

### Build fails
- Проверьте, что Root Directory установлен в `frontend`
- Убедитесь, что все зависимости в `package.json`

## Production Checklist

- [ ] Supabase SQL схема выполнена
- [ ] Переменные окружения настроены в Vercel
- [ ] Backend API задеплоен и доступен
- [ ] `NEXT_PUBLIC_API_URL` указывает на production backend
- [ ] Тестирование на production URL

