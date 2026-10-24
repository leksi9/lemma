"""Собирает app/index.html из doska.html (общий исходник для браузера и приложения)."""
import pathlib, sys
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '../doska.html').read_text(encoding='utf-8')
html = ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<script>window.DOSKA_APP=true;</script>\n'
        '<style>[hidden]{display:none!important}body{margin:0}</style>\n'
        '</head>\n<body>\n' + src + '\n</body>\n</html>\n')
out = pathlib.Path(__file__).parent / 'app' / 'index.html'
out.write_text(html, encoding='utf-8')
print('ok', out, len(html))
