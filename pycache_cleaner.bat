@echo off
setlocal EnableExtensions

set "TARGET_DIR=%~1"
if not defined TARGET_DIR set "TARGET_DIR=%CD%"

if not exist "%TARGET_DIR%" (
    echo Target directory does not exist: "%TARGET_DIR%"
    exit /b 1
)

pushd "%TARGET_DIR%" >nul 2>&1 || (
    echo Failed to access directory: "%TARGET_DIR%"
    exit /b 1
)

echo Cleaning __pycache__ directories in "%CD%"...
set "REMOVED_COUNT=0"
for /f "delims=" %%D in ('powershell -NoProfile -Command "$root = '%TARGET_DIR%'; Get-ChildItem -LiteralPath $root -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '__pycache__' } | ForEach-Object { $_.FullName }"') do (
    echo Removing "%%~fD"
    rd /s /q "%%~fD" 2>nul
    if not exist "%%~fD" set /a REMOVED_COUNT+=1
)

if "%REMOVED_COUNT%"=="0" (
    echo No __pycache__ directories found.
) else (
    echo Removed %REMOVED_COUNT% __pycache__ directory/ies.
)

popd >nul
endlocal
exit /b 0