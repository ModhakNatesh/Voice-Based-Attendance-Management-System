@echo off
echo VBAMS - Voice Based Attendance System
echo =======================================
echo.

REM Check Python installation
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check and install requirements
python -c "import PyQt5" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install requirements
        pause
        exit /b 1
    )
    echo Requirements installed successfully!
)

REM Run the application
echo Starting VBAMS...
python main.py
REM Don't treat window close as an error
echo Application closed.
exit /b 1