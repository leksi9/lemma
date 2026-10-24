@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python не найден. Установите Python 3.12 с python.org ^(галочка "Add to PATH"^).
  pause
  exit /b 1
)
echo Ставлю pywebview и pyinstaller...
%PY% -m pip install --upgrade pywebview pyinstaller || goto :fail
echo Собираю Doska.exe...
%PY% -m PyInstaller --noconfirm --clean --windowed --name Doska --icon doska.ico --add-data "app;app" doska.py || goto :fail
echo Кладу страницу доски рядом с exe...
xcopy /E /I /Y app dist\Doska\app >nul || goto :fail
echo.
echo Готово: dist\Doska\Doska.exe
echo Больше собирать не нужно. Чтобы обновить доску, замените файл
echo app\index.html в папке рядом с Doska.exe.
explorer dist\Doska
pause
exit /b 0
:fail
echo Сборка не удалась. Подробности выше.
pause
exit /b 1
