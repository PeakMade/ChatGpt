@echo off
echo ===============================================
echo PostgreSQL Installation and Setup for Windows
echo ===============================================
echo.
echo Step 1: Download PostgreSQL
echo Please download PostgreSQL 15 or later from:
echo https://www.postgresql.org/download/windows/
echo.
echo Step 2: Installation Notes
echo - Use default port: 5432
echo - Remember the password for 'postgres' user
echo - Install Stack Builder components if asked
echo.
echo Step 3: After Installation, run these commands in psql:
echo.
echo CREATE DATABASE chatgpt_multiuser;
echo CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';
echo GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;
echo.
echo Step 4: Test connection
echo psql -h localhost -U chatgpt_app -d chatgpt_multiuser
echo.
echo Step 5: Run migration
echo python migrate_database.py
echo.
pause
