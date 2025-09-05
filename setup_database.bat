@echo off
echo ========================================
echo PostgreSQL Database Setup for ChatGPT
echo ========================================
echo.
echo This script will create the database and user for your ChatGPT app
echo.

REM Prompt for postgres password
set /p POSTGRES_PASSWORD="Enter the postgres user password you set during installation: "

echo.
echo Creating database and user...
echo.

REM Create the SQL commands in a temporary file
echo CREATE DATABASE chatgpt_multiuser; > setup_db.sql
echo CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123'; >> setup_db.sql
echo GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app; >> setup_db.sql
echo ALTER USER chatgpt_app CREATEDB; >> setup_db.sql
echo \q >> setup_db.sql

REM Execute the SQL commands
psql -U postgres -h localhost -f setup_db.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Database and user created!
    echo.
    echo Database: chatgpt_multiuser
    echo Username: chatgpt_app
    echo Password: secure_password_123
    echo Host: localhost
    echo Port: 5432
    echo.
    echo You can now run the migration script!
) else (
    echo.
    echo ERROR: Failed to create database or user
    echo Please check your postgres password and try again
)

REM Clean up
del setup_db.sql

echo.
pause
