@echo off
echo ========================================
echo PostgreSQL Password Reset
echo ========================================
echo.
echo This will reset the postgres user password
echo.

REM Stop PostgreSQL service
echo Step 1: Stopping PostgreSQL service...
net stop postgresql-x64-16
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Could not stop service automatically
    echo Please manually stop "postgresql-x64-16" service in Services
    pause
)

echo.
echo Step 2: Modifying authentication settings...

REM Backup original pg_hba.conf
copy "C:\Program Files\PostgreSQL\16\data\pg_hba.conf" "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.backup" >nul 2>&1

REM Create temporary pg_hba.conf with trust authentication
echo # Temporary configuration for password reset > "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp"
echo local   all             all                                     trust >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp"
echo host    all             all             127.0.0.1/32            trust >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp"
echo host    all             all             ::1/128                 trust >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp"

REM Replace original with temp
copy "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp" "C:\Program Files\PostgreSQL\16\data\pg_hba.conf" >nul 2>&1
del "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.temp" >nul 2>&1

echo.
echo Step 3: Starting PostgreSQL service...
net start postgresql-x64-16
if %ERRORLEVEL% NEQ 0 (
    echo Error: Could not start PostgreSQL service
    echo Please manually start "postgresql-x64-16" service in Services
    pause
    exit /b 1
)

echo.
echo Step 4: Setting new password...
timeout /t 3 /nobreak >nul

REM Set new password
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d postgres -c "ALTER USER postgres PASSWORD 'postgres123';"
if %ERRORLEVEL% EQU 0 (
    echo ✅ Password set successfully!
    echo New password: postgres123
) else (
    echo ❌ Failed to set password
)

echo.
echo Step 5: Restoring secure authentication...

REM Restore original pg_hba.conf or create secure one
if exist "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.backup" (
    copy "C:\Program Files\PostgreSQL\16\data\pg_hba.conf.backup" "C:\Program Files\PostgreSQL\16\data\pg_hba.conf" >nul 2>&1
) else (
    echo # Secure configuration > "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
    echo local   all             all                                     md5 >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
    echo host    all             all             127.0.0.1/32            md5 >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
    echo host    all             all             ::1/128                 md5 >> "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
)

echo.
echo Step 6: Restarting PostgreSQL with secure settings...
net stop postgresql-x64-16 >nul 2>&1
timeout /t 2 /nobreak >nul
net start postgresql-x64-16 >nul 2>&1

echo.
echo ========================================
echo ✅ Password Reset Complete!
echo ========================================
echo.
echo New postgres password: postgres123
echo.
echo Now you can connect in pgAdmin with:
echo   Username: postgres
echo   Password: postgres123
echo.
echo Or create database directly:
pause
