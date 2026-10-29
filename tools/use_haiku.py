#!/usr/bin/env python3
"""Switch Crow's mind to Claude Haiku 5.5 (or back to local Qwen) without editing files by hand.

    python3 tools/use_haiku.py          # asks for your Anthropic API key, tests it, saves it privately
    python3 tools/use_haiku.py --off    # back to the local model (the key stays saved)

The key is stored only in crow-config.json in this folder, which Git ignores,
with permissions that only your user can read. It is never shown in the
browser view or sent anywhere except api.anthropic.com. Restart Crow afterwards.
"""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'crow-config.json'
MODEL = 'claude-haiku-5-5'


def save(settings):
    tmp = CONFIG.with_suffix('.tmp')
    tmp.write_text(json.dumps(settings, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG)


def test(key):
    body = {'model': MODEL, 'max_tokens': 20, 'messages': [{'role': 'user', 'content': 'Reply with the word ready.'}]}
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=json.dumps(body).encode(),
                                 headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--off', action='store_true', help='Use the local Qwen model again.')
    parser.add_argument('--daily-budget', type=float, default=None, help='Daily cloud spend cap in US dollars (default 1.00).')
    args = parser.parse_args()
    settings = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    if args.off:
        settings['model_provider'] = 'ollama'
        save(settings)
        print('Crow will use the local model after his next restart.')
        return
    key = settings.get('anthropic_api_key', '')
    if not key or input('A key is already saved. Replace it? [y/N] ').strip().lower() == 'y':
        key = getpass.getpass('Paste your Anthropic API key (it will not be shown): ').strip()
    if not key:
        sys.exit('No key entered; nothing changed.')
    try:
        test(key)
    except urllib.error.HTTPError as exc:
        sys.exit(f'The key was not accepted ({exc.code}: {exc.read().decode(errors="replace")[:200]}). Nothing changed.')
    except OSError as exc:
        sys.exit(f'Could not reach Anthropic ({exc}). Nothing changed.')
    settings.update(model_provider='anthropic', anthropic_model=MODEL, anthropic_api_key=key)
    settings.setdefault('daily_budget_usd', 1.0)
    if args.daily_budget is not None:
        settings['daily_budget_usd'] = args.daily_budget
    save(settings)
    print(f'Key works. Crow will think with {MODEL} after his next restart, up to ${settings["daily_budget_usd"]:.2f} a day, '
          'then fall back to the local model for the rest of that day.')


if __name__ == '__main__':
    main()
