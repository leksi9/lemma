@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python не найден. Установите Python 3.12 с python.org ^(галочка "Add to PATH"^)
  echo или запустите этот файл из Anaconda Prompt.
  pause
  exit /b 1
)
%PY% -c "import webview" 2>nul
if errorlevel 1 (
  echo Устанавливаю pywebview - это нужно один раз...
  %PY% -m pip install --upgrade pywebview
  if errorlevel 1 (
    echo Не получилось установить pywebview. Подробности выше.
    pause
    exit /b 1
  )
)
start "" %PY% -c "import runpy,ctypes;ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(),0);runpy.run_path('doska.py',run_name='__main__')"
