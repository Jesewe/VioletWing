@echo off
setlocal
echo Cleaning __pycache__ directories in %CD%...
for /f "delims=" %%D in ('dir /s /b /ad "__pycache__" 2^>nul') do (
    echo Removing "%%D"
    rd /s /q "%%D"
)
echo Done.
endlocal