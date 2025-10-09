@echo off
echo ========================================
echo ChatGPT Database Migration
echo ========================================
echo.

REM Test PostgreSQL connection first
echo Testing PostgreSQL connection...
psql -U chatgpt_app -d chatgpt_multiuser -h localhost -c "\l"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Cannot connect to PostgreSQL database
    echo Please ensure:
    echo 1. PostgreSQL is running
    echo 2. Database 'chatgpt_multiuser' exists
    echo 3. User 'chatgpt_app' has access
    echo.
    echo Run setup_database.bat first if you haven't already
    pause
    exit /b 1
)

echo.
echo SUCCESS: PostgreSQL connection working!
echo.
echo Running migration script...
echo.

REM Run the Python migration script
C:\Users\tgaskins\AppData\Local\Programs\Python\Python313\python.exe migrate_database.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo MIGRATION COMPLETED SUCCESSFULLY!
    echo ========================================
    echo.
    echo Your ChatGPT app is now ready for multi-user support!
    echo.
    echo Default migrated user:
    echo Username: migrated_user
    echo Password: changeme123
    echo.
    echo You can now run your app:
    echo python app.py
    echo.
) else (
    echo.
    echo ERROR: Migration failed
    echo Check the error messages above
)

pause
