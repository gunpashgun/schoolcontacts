# Quick Start Guide

## 1. Supabase Setup ✅

Supabase уже настроен:
- **Project URL**: `https://tzcdzyqhadczxsvvfdhg.supabase.co`
- **Service Role Key**: добавлен в `.env` (локально)
- **Anon Key**: `sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I`

### Выполнить SQL схему:

1. Откройте Supabase Dashboard: https://supabase.com/dashboard/project/tzcdzyqhadczxsvvfdhg
2. Перейдите в **SQL Editor**
3. Создайте новый запрос
4. Скопируйте содержимое файла `supabase_schema.sql`
5. Нажмите **Run**

Это создаст таблицы: `jobs`, `school_results`, `person_leads`

## 2. Backend Setup

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Установить зависимости (если еще не установлены)
pip install -r requirements.txt

# Проверить .env файл
cat .env | grep SUPABASE
```

## 3. Frontend Setup

```bash
cd frontend

# Создать .env.local
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=https://tzcdzyqhadczxsvvfdhg.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_mBHUGJABWYTE4PahfMcmSA_MOUETx-I
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Установить зависимости (если еще не установлены)
npm install
```

## 4. Запуск

### Backend API:
```bash
cd api
uvicorn main:app --reload --port 8000
```

### Frontend:
```bash
cd frontend
npm run dev
```

Откройте http://localhost:3000

## 5. Тестирование

1. Введите список школ в формате:
```
PPPK Petra - Private Christian (Elementary to High School, Education Board/Group)
Yohanes Gabriel Foundation - Private Catholic (Elementary to High School, Religious Foundation)
```

2. Нажмите "Process Schools"
3. Дождитесь завершения обработки
4. Просмотрите результаты и скачайте их

## Важно!

- **Service Role Key** находится только в локальном `.env` файле
- **НЕ коммитьте** `.env` в Git (он уже в `.gitignore`)
- Для продакшена используйте переменные окружения на сервере

