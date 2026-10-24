"""Лемма — доска для уроков, настольное приложение (Windows).

Запуск:  pythonw doska.py   (или двойной клик по «Запустить доску.bat»)
Нужно:   Python 3.9+ и пакет pywebview (pip install pywebview).
Окно рисуется движком Microsoft Edge WebView2 — он уже есть в Windows 10/11,
поэтому перо планшета с нажимом работает так же, как в браузере.
"""
import base64
import json
import subprocess
import tempfile
import threading
import time
import urllib.request
import http.server
import functools
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
REPO = "leksi9/lemma"
try:
    from _version import VERSION  # файл создаётся при сборке установщика
except ImportError:
    VERSION = ""  # запуск из исходников: автообновление выключено
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


def _vtuple(v):
    try:
        return tuple(int(x) for x in str(v).lstrip("vV").split("."))
    except ValueError:
        return ()


def _http(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Lemma-Updater", "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout)


class Api:
    """Функции, которые страница вызывает через window.pywebview.api."""

    _update = None

    def app_version(self):
        return VERSION

    def check_update(self):
        """Спрашиваем GitHub о последней версии. Ничего не скачиваем."""
        if not VERSION or not getattr(sys, "frozen", False):
            return {"ok": True, "available": False, "current": VERSION, "dev": True}
        try:
            with _http(f"https://api.github.com/repos/{REPO}/releases/latest") as r:
                rel = json.loads(r.read().decode("utf-8"))
        except Exception as e:  # нет интернета и т.п.
            return {"ok": False, "error": str(e), "current": VERSION}
        latest = str(rel.get("tag_name", "")).lstrip("vV")
        asset = next((a for a in rel.get("assets", []) if str(a.get("name", "")).lower().endswith("setup.exe")), None)
        available = bool(asset) and _vtuple(latest) > _vtuple(VERSION)
        Api._update = {"version": latest, "url": asset["browser_download_url"], "size": asset.get("size", 0)} if available else None
        return {"ok": True, "available": available, "current": VERSION, "latest": latest,
                "notes": rel.get("body") or "", "size": asset.get("size", 0) if asset else 0}

    def install_update(self):
        """Скачиваем установщик в фоне, сообщаем странице прогресс, затем ставим тихо и перезапускаемся."""
        upd = Api._update
        if not upd:
            return False
        threading.Thread(target=self._download_and_run, args=(upd,), daemon=True).start()
        return True

    def _js(self, code):
        try:
            webview.windows[0].evaluate_js(code)
        except Exception:
            pass

    def _download_and_run(self, upd):
        path = os.path.join(tempfile.gettempdir(), f"Lemma-Setup-{upd['version']}.exe")
        try:
            with _http(upd["url"], timeout=60) as r, open(path + ".part", "wb") as f:
                total = int(r.headers.get("Content-Length") or upd.get("size") or 0)
                done, last = 0, 0.0
                while True:
                    chunk = r.read(256 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total and time.time() - last > 0.15:
                        last = time.time()
                        self._js(f"window.onUpdateProgress&&onUpdateProgress({done / total:.3f})")
            if upd.get("size") and os.path.getsize(path + ".part") != upd["size"]:
                raise IOError("файл скачался не полностью")
            os.replace(path + ".part", path)
        except Exception as e:
            self._js("window.onUpdateFailed&&onUpdateFailed(" + json.dumps(str(e)) + ")")
            return
        self._js("window.onUpdateProgress&&onUpdateProgress(1)")
        self._js("window.onUpdateInstalling&&onUpdateInstalling()")
        time.sleep(1.2)  # даём странице дописать доски
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        try:
            subprocess.Popen([path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"],
                             creationflags=flags, close_fds=True)
        except Exception as e:
            self._js("window.onUpdateFailed&&onUpdateFailed(" + json.dumps(str(e)) + ")")
            return
        for w in list(webview.windows):
            try:
                w.destroy()
            except Exception:
                pass

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


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Отдаёт страницу доски. HTML не кэшируется, файлы версии (в папке с её отпечатком) кэшируются навсегда."""

    def end_headers(self):
        if self.path.split("?")[0].endswith((".html", "/")):
            self.send_header("Cache-Control", "no-store, max-age=0")
        else:
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        super().end_headers()

    def log_message(self, *args):  # без консоли (pythonw) печать падает
        pass


def serve(root):
    """Свой маленький сервер на прежнем адресе 127.0.0.1:PORT — так доски остаются на месте.
    Если порт занят (Лемма уже открыта), используем уже работающий сервер."""
    handler = functools.partial(_Handler, directory=root)
    try:
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    except OSError:
        return None
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    index = fresh_copy(find_index())
    web = os.path.join(data_dir(), "web")
    if os.path.dirname(os.path.dirname(index)) == web:
        serve(web)
        # адрес содержит отпечаток версии: новая версия = новый адрес, старая копия из кэша не подхватится
        url = f"http://127.0.0.1:{PORT}/{os.path.basename(os.path.dirname(index))}/index.html"
        http_server = False
    else:  # не удалось скопировать страницу — запасной путь, как раньше
        url, http_server = index, True
    win_kwargs = only_supported(
        webview.create_window,
        title=APP_NAME,
        url=url,
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
        http_server=http_server,
        http_port=PORT,
        debug=("--debug" in sys.argv),
    )
    webview.start(**start_kwargs)


if __name__ == "__main__":
    main()
