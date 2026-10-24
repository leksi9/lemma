@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Копирует новую версию доски в уже собранный Lemma.exe — без пересборки.
set TARGET=
if exist "dist\Lemma\Lemma.exe" set TARGET=dist\Lemma
if not defined TARGET if exist "%~dp0..\Lemma.exe" set TARGET=%~dp0..
if not defined TARGET (
  echo Не нашёл Lemma.exe.
  echo Перетащите сюда папку, где лежит Lemma.exe, и нажмите Enter:
  set /p TARGET=
)
set TARGET=%TARGET:"=%
if not exist "%TARGET%\Lemma.exe" (
  echo В папке "%TARGET%" нет Lemma.exe.
  pause
  exit /b 1
)
taskkill /im Lemma.exe /f >nul 2>nul
xcopy /E /I /Y app "%TARGET%\app" >nul
echo Готово, доска обновлена. Запускайте Lemma.exe как обычно.
pause
