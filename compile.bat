@echo off
setlocal enabledelayedexpansion

:: Set variables
set "PROJECT_NAME=VioletWing"
set "MAIN_FILE=main.py"
set "OUTPUT_DIR=output"
set "ICON_FILE=src\img\icon.ico"
set "VERSION_FILE=version.txt"

:: Display header
echo ========================================
echo      VioletWing Build Script
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if PyInstaller is available
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

:: Check if main file exists
if not exist "%MAIN_FILE%" (
    echo ERROR: Main file '%MAIN_FILE%' not found
    pause
    exit /b 1
)

:: Check if icon file exists
if not exist "%ICON_FILE%" (
    echo WARNING: Icon file '%ICON_FILE%' not found
    set "ICON_PARAM="
) else (
    set "ICON_PARAM=--icon "%ICON_FILE%""
)

:: Check if version file exists
if not exist "%VERSION_FILE%" (
    echo WARNING: Version file '%VERSION_FILE%' not found
    set "VERSION_PARAM="
) else (
    set "VERSION_PARAM=--version-file "%VERSION_FILE%""
)

:: Cleaning up cache directories...
echo Cleaning up cache directories...
if exist "classes\__pycache__" rmdir /s /q "classes\__pycache__" 2>nul
if exist "gui\__pycache__" rmdir /s /q "gui\__pycache__" 2>nul
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul

:: Find and remove all __pycache__ directories
for /d /r . %%d in (*__pycache__*) do (
    if exist "%%d" (
        echo Removing: %%d
        rmdir /s /q "%%d" 2>nul
    )
)

:: Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build" 2>nul
if exist "%PROJECT_NAME%.spec" del /q "%PROJECT_NAME%.spec" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

:: Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
echo Starting compilation...
echo ========================================

:: Build the PyInstaller command
set "PYINSTALLER_CMD=pyinstaller --noconfirm --onefile --windowed"
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% %ICON_PARAM%"
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --name "%PROJECT_NAME%""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% %VERSION_PARAM%"
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "classes;classes/""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "gui;gui/""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "constants;constants/""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "src/assets/*;src/assets""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "src/fonts/*;src/fonts""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "src/*;src""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% --distpath "%OUTPUT_DIR%""
set "PYINSTALLER_CMD=%PYINSTALLER_CMD% "%MAIN_FILE%""

:: Execute PyInstaller
%PYINSTALLER_CMD%

:: Check compilation result
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Compilation failed!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo Compilation complete.
echo.

:: Verify executable was created
if exist "%OUTPUT_DIR%\%PROJECT_NAME%.exe" (
    echo ========================================
    echo SUCCESS: Executable created successfully!
    echo Location: %OUTPUT_DIR%\%PROJECT_NAME%.exe
    
    :: Get file size
    for %%A in ("%OUTPUT_DIR%\%PROJECT_NAME%.exe") do (
        set "FILE_SIZE=%%~zA"
        set /a "FILE_SIZE_MB=!FILE_SIZE! / 1024 / 1024"
        echo Size: !FILE_SIZE_MB! MB
    )
    echo ========================================
) else (
    echo ========================================
    echo ERROR: Executable not found in %OUTPUT_DIR%
    echo ========================================
    pause
    exit /b 1
)

:: Final cleanup
echo.
echo Performing final cleanup...
if exist "build" rmdir /s /q "build" 2>nul
if exist "%PROJECT_NAME%.spec" del /q "%PROJECT_NAME%.spec" 2>nul

echo Cleanup complete.
echo.
echo ========================================
echo Build process completed successfully!
echo ========================================
echo.

:: Ask if user wants to run the executable
set /p "RUN_EXE=Do you want to run %PROJECT_NAME%.exe? (y/n): "
if /i "!RUN_EXE!"=="y" (
    echo Running %PROJECT_NAME%.exe...
    start "" "%OUTPUT_DIR%\%PROJECT_NAME%.exe"
)

pause