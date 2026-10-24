"""Лемма — доска для уроков, настольное приложение (Windows).

Запуск:  pythonw doska.py   (или двойной клик по «Запустить доску.bat»)
Нужно:   Python 3.9+ и пакет pywebview (pip install pywebview).
Окно рисуется движком Microsoft Edge WebView2 — он уже есть в Windows 10/11,
поэтому перо планшета с нажимом работает так же, как в браузере.
"""
import base64
import hashlib
import shutil
import inspect
import mimetypes
import os
import sys

import webview

mimetypes.add_type("application/wasm", ".wasm")  # иначе Python для блока кода не загрузится
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")

APP_NAME = "Лемма"
PORT = 47321  # постоянный порт: от него зависит, где браузерный движок хранит доски


def find_index():
    """Сначала ищем app\\index.html рядом с Doska.exe — его можно заменять без пересборки.
    Если его там нет, берём копию, вшитую в exe."""
    here = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    candidates = [os.path.join(here, "app", "index.html")]
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(getattr(sys, "_MEIPASS", here), "app", "index.html"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[0]


def fresh_copy(index):
    """Кладём страницу в папку с именем по её содержимому. Новая версия = новый адрес,
    поэтому движок окна никогда не покажет старую закэшированную страницу."""
    try:
        with open(index, "rb") as f:
            digest = hashlib.md5(f.read()).hexdigest()[:12]
        web = os.path.join(data_dir(), "web")
        target_dir = os.path.join(web, digest)
        target = os.path.join(target_dir, "index.html")
        if not os.path.isfile(target):
            tmp = target_dir + ".tmp"
            shutil.rmtree(tmp, ignore_errors=True)
            # вся папка app: страница и Python для блока кода (pyodide)
            shutil.copytree(os.path.dirname(index), tmp)
            os.replace(tmp, target_dir)
        for name in os.listdir(web):
            if name != digest and not name.endswith(".tmp"):
                shutil.rmtree(os.path.join(web, name), ignore_errors=True)
        return target
    except OSError:
        return index


def data_dir():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(root, "Doska")  # прежнее имя папки: тут лежат все доски, не менять
    os.makedirs(path, exist_ok=True)
    return path


def only_supported(func, **kwargs):
    """Передаём только те параметры, которые понимает установленная версия pywebview."""
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return kwargs
    if any(p.kind == p.VAR_KEYWORD for p in params.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in params}


def save_dialog_type():
    fd = getattr(webview, "FileDialog", None)
    if fd is not None and hasattr(fd, "SAVE"):
        return fd.SAVE
    return webview.SAVE_DIALOG


class Api:
    """Функции, которые страница вызывает через window.pywebview.api."""

    def save_file(self, name, b64data):
        win = webview.windows[0]
        ext = os.path.splitext(name)[1].lower()
        types = {
            ".png": ("Картинка PNG (*.png)",),
            ".doska": ("Файл доски (*.doska)",),
            ".pdf": ("Документ PDF (*.pdf)",),
        }.get(ext, ("Все файлы (*.*)",))
        kwargs = only_supported(
            win.create_file_dialog,
            dialog_type=save_dialog_type(),
            save_filename=name,
            file_types=types,
            directory=os.path.join(os.path.expanduser("~"), "Documents"),
        )
        try:
            res = win.create_file_dialog(**kwargs)
        except Exception:
            kwargs.pop("file_types", None)
            res = win.create_file_dialog(**kwargs)
        if not res:
            return False
        path = res if isinstance(res, str) else res[0]
        if ext and not path.lower().endswith(ext):
            path += ext
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64data))
        return os.path.basename(path)


def main():
    index = fresh_copy(find_index())
    win_kwargs = only_supported(
        webview.create_window,
        title=APP_NAME,
        url=index,
        js_api=Api(),
        width=1400,
        height=900,
        min_size=(820, 560),
        background_color="#FFFFFF",
        maximized=True,
        text_select=True,
        zoomable=False,
    )
    webview.create_window(**win_kwargs)

    start_kwargs = only_supported(
        webview.start,
        private_mode=False,          # иначе доски не сохраняются между запусками
        storage_path=data_dir(),
        http_server=True,
        http_port=PORT,
        debug=("--debug" in sys.argv),
    )
    webview.start(**start_kwargs)


if __name__ == "__main__":
    main()
