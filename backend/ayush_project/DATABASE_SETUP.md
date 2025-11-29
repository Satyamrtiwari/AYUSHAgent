# Database Setup Guide - Neotech PostgreSQL

## 📍 Where Data is Stored

### Frontend (React/Vite)
- **Only stores JWT tokens** in `localStorage` (for authentication)
- **NO user data, patients, or diagnoses** are stored in the frontend
- All data comes from the backend API

### Backend (Django)
- **ALL data is stored in the database** configured in `settings.py`:
  - ✅ **Users** (Django's built-in User model)
  - ✅ **Patients** (Patient model)
  - ✅ **Diagnoses** (Diagnosis model)
  - ✅ **Audit Logs** (AuditLog model)

## 🔧 How to Connect to Neotech Database

### Step 1: Get Your Neotech Database URL

From your Neotech dashboard, copy your PostgreSQL connection string. It should look like:
```
postgresql://username:password@host:port/database_name
```

### Step 2: Set the DATABASE_URL Environment Variable

**Option A: Create a `.env` file** (recommended for local development)

Create a file named `.env` in `backend/ayush_project/` with:
```env
DATABASE_URL=postgresql://your_username:your_password@your_host:5432/your_database
```

**Option B: Set as System Environment Variable** (Windows PowerShell)
```powershell
$env:DATABASE_URL="postgresql://your_username:your_password@your_host:5432/your_database"
```

**Option C: For Production/Deployment**
Set `DATABASE_URL` in your hosting platform's environment variables (Render, Railway, Vercel, etc.)

### Step 3: Install PostgreSQL Driver

Make sure `psycopg2-binary` is installed:
```bash
pip install psycopg2-binary
```

### Step 4: Run Migrations

After setting `DATABASE_URL`, run migrations to create tables in your Neotech database:
```bash
cd backend/ayush_project
python manage.py migrate
```

### Step 5: Verify Connection

Start your Django server:
```bash
python manage.py runserver
```

You should see in the console:
```
✅ Using PostgreSQL database: your_host/your_database
```

## 🔍 How It Works

1. **settings.py** checks for `DATABASE_URL` environment variable
2. If found → uses **PostgreSQL (Neotech)**
3. If not found → falls back to **SQLite (local)**
4. **All Django models** automatically use the configured database:
   - `User.objects.all()` → Neotech DB
   - `Patient.objects.create()` → Neotech DB
   - `Diagnosis.objects.filter()` → Neotech DB
   - `AuditLog.objects.create()` → Neotech DB

## ✅ Verification

To verify data is going to Neotech:
1. Create a user/patient through the frontend
2. Check your Neotech database dashboard
3. You should see the data there (not in local `db.sqlite3`)

## 🚨 Troubleshooting

**Problem**: Still using SQLite
- **Solution**: Make sure `DATABASE_URL` is set and Django server is restarted

**Problem**: `psycopg2` module not found
- **Solution**: `pip install psycopg2-binary` in your virtual environment

**Problem**: Connection refused
- **Solution**: Check your Neotech database URL, credentials, and network access

