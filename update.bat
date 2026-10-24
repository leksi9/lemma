@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Копирует новую версию доски в уже собранный Doska.exe — без пересборки.
set TARGET=
if exist "dist\Doska\Doska.exe" set TARGET=dist\Doska
if not defined TARGET if exist "%~dp0..\Doska.exe" set TARGET=%~dp0..
if not defined TARGET (
  echo Не нашёл Doska.exe.
  echo Перетащите сюда папку, где лежит Doska.exe, и нажмите Enter:
  set /p TARGET=
)
set TARGET=%TARGET:"=%
if not exist "%TARGET%\Doska.exe" (
  echo В папке "%TARGET%" нет Doska.exe.
  pause
  exit /b 1
)
taskkill /im Doska.exe /f >nul 2>nul
xcopy /E /I /Y app "%TARGET%\app" >nul
echo Готово, доска обновлена. Запускайте Doska.exe как обычно.
pause
