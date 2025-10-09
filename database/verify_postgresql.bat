@echo off
echo ========================================
echo PostgreSQL Installation Verification
echo ========================================
echo.
echo Testing PostgreSQL installation...
echo.

REM Test if PostgreSQL is installed
psql --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PostgreSQL not found in PATH
    echo Please add C:\Program Files\PostgreSQL\16\bin to your PATH
    echo Or restart your computer after installation
    pause
    exit /b 1
)

echo.
echo SUCCESS: PostgreSQL is installed!
echo.
echo Testing service status...
sc query postgresql-x64-16
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: PostgreSQL service not found or not running
    echo Trying to start service...
    net start postgresql-x64-16
)

echo.
echo ========================================
echo Installation verification complete!
echo ========================================
pause
