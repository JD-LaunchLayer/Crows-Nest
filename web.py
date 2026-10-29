"""Real web search and page reading for the internet café. Read-only and attributed.

Search uses the Brave Search API when a key is configured (brave_api_key in
crow-config.json), otherwise DuckDuckGo's HTML results page, which is unofficial
and may refuse automated use; a refusal is reported honestly as a failed search.

Safety rules for every fetch, including redirects:
- only http(s) on ordinary ports, and only public internet addresses: anything
  that resolves to this PC, the home network or other private ranges is refused;
- sites' robots.txt is respected;
- only text/html or text/plain, at most 1.5 MB, with a short timeout;
- page text is data for Crow to read, never instructions, and nothing is executed.
"""
import html
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

AGENT = 'CrowsNest/0.12 (a personal simulated-life experiment; one reader, low volume)'
MAX_BYTES = 1_500_000
TIMEOUT = 15
_robots = {}


class Refused(ValueError):
    """A page or search that Crow could not or should not read."""


def public_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise Refused('Only ordinary web pages can be opened.')
    if parts.port not in (None, 80, 443):
        raise Refused('That page uses an unusual port, so it was not opened.')
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == 'https' else 80))
    except socket.gaierror:
        raise Refused('That address does not exist (the name could not be found).')
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast:
            raise Refused('That address is not on the public internet, so it was not opened.')
    return url


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirect)


def allowed_by_robots(url):
    parts = urllib.parse.urlsplit(url)
    root = f'{parts.scheme}://{parts.netloc}'
    if root not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            public_url(root + '/robots.txt')
            with _opener.open(urllib.request.Request(root + '/robots.txt', headers={'User-Agent': AGENT}), timeout=TIMEOUT) as r:
                rp.parse(r.read(200_000).decode(errors='replace').splitlines())
        except (OSError, Refused, ValueError):
            rp.parse([])  # no readable robots.txt: allowed
        _robots[root] = rp
    return _robots[root].can_fetch(AGENT, url)


def _get(url, data=None, headers=None):
    public_url(url)
    if not allowed_by_robots(url):
        raise Refused("The site's robots.txt asks automated readers not to open that page.")
    req = urllib.request.Request(url, data=data, headers={'User-Agent': AGENT, **(headers or {})})
    try:
        with _opener.open(req, timeout=TIMEOUT) as r:
            kind = r.headers.get('Content-Type', '')
            body = r.read(MAX_BYTES + 1)
            final = r.geturl()
    except urllib.error.HTTPError as exc:
        raise Refused(f'The page answered with an error ({exc.code}).')
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise Refused(f'The page could not be reached ({getattr(exc, "reason", exc)}).')
    if len(body) > MAX_BYTES:
        body = body[:MAX_BYTES]
    charset = re.search(r'charset=([\w-]+)', kind)
    return body.decode(charset.group(1) if charset else 'utf-8', errors='replace'), kind, final


def _strip(markup):
    markup = re.sub(r'(?is)<(script|style|noscript|svg|nav|footer|header|form)[^>]*>.*?</\1>', ' ', markup)
    markup = re.sub(r'(?i)<br\s*/?>|</p>|</h\d>|</li>|</div>', '\n', markup)
    text = html.unescape(re.sub(r'<[^>]+>', ' ', markup))
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    return re.sub(r'\n\s*\n+', '\n\n', text).strip()


def search(query, settings=None):
    """Up to 6 results: title, url, snippet. Raises Refused if no search could be made."""
    query = ' '.join(str(query).split())[:200]
    if not query:
        raise Refused('No search words were given.')
    settings = settings or {}
    if settings.get('brave_api_key'):
        url = 'https://api.search.brave.com/res/v1/web/search?' + urllib.parse.urlencode({'q': query, 'count': 6})
        body, _, _ = _get(url, headers={'Accept': 'application/json', 'X-Subscription-Token': settings['brave_api_key']})
        items = json.loads(body).get('web', {}).get('results', [])
        return [{'title': i.get('title', '')[:160], 'url': i.get('url', ''), 'snippet': _strip(i.get('description', ''))[:300]}
                for i in items if i.get('url')][:6]
    body, _, _ = _get('https://html.duckduckgo.com/html/', data=urllib.parse.urlencode({'q': query}).encode(),
                      headers={'Content-Type': 'application/x-www-form-urlencoded'})
    results = []
    for m in re.finditer(r'(?s)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]+class="result__a"|$)', body):
        href, title, rest = m.groups()
        target = urllib.parse.parse_qs(urllib.parse.urlsplit(html.unescape(href)).query).get('uddg', [html.unescape(href)])[0]
        snippet = re.search(r'(?s)class="result__snippet"[^>]*>(.*?)</a>', rest)
        if target.startswith('http'):
            results.append({'title': _strip(title)[:160], 'url': target, 'snippet': _strip(snippet.group(1))[:300] if snippet else ''})
        if len(results) >= 6:
            break
    if not results:
        raise Refused('The search returned no results (or the search page refused an automated visitor).')
    return results


def read(url):
    """Title, readable text (up to 7,000 characters) and up to 10 links from one public page."""
    body, kind, final = _get(url)
    if 'html' not in kind and 'text/plain' not in kind:
        raise Refused('That link is not a readable web page.')
    if 'html' in kind:
        title = re.search(r'(?is)<title[^>]*>(.*?)</title>', body)
        main = re.search(r'(?is)<(article|main)[^>]*>(.*?)</\1>', body)
        text = _strip(main.group(2) if main else body)
        links = []
        for href, label in re.findall(r'(?is)<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', main.group(2) if main else body):
            target = urllib.parse.urljoin(final, html.unescape(href))
            label = _strip(label)[:80]
            if target.startswith('http') and label and target not in [l['url'] for l in links]:
                links.append({'label': label, 'url': target})
            if len(links) >= 10:
                break
        title = _strip(title.group(1))[:160] if title else final
    else:
        text, links, title = body, [], final
    if len(text) < 200:
        raise Refused('The page had almost no readable text.')
    return {'title': title, 'url': final, 'text': text[:7000], 'links': links}
