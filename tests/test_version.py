"""The page and the server must report the same version, or the browser reloads forever."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
server=re.search(r"APP_VERSION = '([\d.]+)'",(ROOT/'crow.py').read_text()).group(1)
html=(ROOT/'index.html').read_text()
page=re.search(r'crow-version" content="([\d.]+)"',html).group(1)
assert server==page, f'crow.py {server} != index.html {page}'
assert f'V{server}' in html, 'visible version label out of date'
print(f'PASS: server and page both v{server}.')
