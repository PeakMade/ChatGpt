@echo off
echo ========================================
echo PostgreSQL Database Setup (Simple)
echo ========================================
echo.
echo Creating database and user for ChatGPT app...
echo.

REM Set PostgreSQL path
set PSQL_PATH="C:\Program Files\PostgreSQL\16\bin\psql.exe"

echo Method 1: Trying to connect as current Windows user...
%PSQL_PATH% -U %USERNAME% -d postgres -c "CREATE DATABASE chatgpt_multiuser;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Database created successfully
    goto create_user
)

echo.
echo Method 2: Trying to connect as postgres user with trust authentication...
%PSQL_PATH% -U postgres -d postgres -c "CREATE DATABASE chatgpt_multiuser;" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Database created successfully
    goto create_user
)

echo.
echo ❌ Could not connect to PostgreSQL automatically
echo.
echo 📋 Manual Setup Required:
echo    1. Open pgAdmin (PostgreSQL administration tool)
echo    2. Or use Command Prompt with postgres password
echo.
echo Would you like to try manual password entry? (y/n)
set /p choice=
if /i "%choice%"=="y" goto manual_setup
goto end

:create_user
echo.
echo Creating application user...
%PSQL_PATH% -U postgres -d postgres -c "CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';"
%PSQL_PATH% -U postgres -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;"
%PSQL_PATH% -U postgres -d postgres -c "ALTER USER chatgpt_app CREATEDB;"
echo ✅ User created successfully
echo.
echo ✅ Database setup complete!
echo    Database: chatgpt_multiuser
echo    User: chatgpt_app
echo    Password: secure_password_123
echo.
goto end

:manual_setup
echo.
echo Enter commands manually in psql:
echo.
echo %PSQL_PATH% -U postgres
echo.
echo Then run these SQL commands:
echo    CREATE DATABASE chatgpt_multiuser;
echo    CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';
echo    GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;
echo    ALTER USER chatgpt_app CREATEDB;
echo    \q
echo.

:end
echo.
echo Setup script completed.
pause
