#!/usr/bin/env python3
"""Look at what Crow has asked for, and stock the trading post (works while he runs).

    python3 tools/stock_shop.py                         # show stock, his credit and his requests
    python3 tools/stock_shop.py add sketchbook "Sketchbook and pencils" 5 2 possession:sketchbook
    python3 tools/stock_shop.py add bread "Fresh loaf (2 servings)" 1 10 pantry:2

add <id> "<name>" <price in credit> <quantity> <effect>
Effects: pantry:N adds N servings of ready food when bought; possession:NAME gives
him an item to keep. Lantern and whetstone have built-in uses; any other
possession is simply something he owns (nothing is invented about what it does).
New stock arrives within about 15 seconds while Crow is running.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    args = sys.argv[1:]
    if not args:
        save = json.loads((ROOT / 'crow-save.json').read_text())
        post = save.get('trading', {})
        print(f"His trade credit: {post.get('credit', 0)}")
        print('In stock:')
        for k, v in post.get('stock', {}).items():
            print(f"  {k}: {v['name']} · {v['price']:g} credit · {v['qty']} left · {v['effect']}")
        print('He has asked for:')
        for r in post.get('requests', []) or [{'item': '(nothing yet)', 'times': 0}]:
            print(f"  {r['item']}" + (f" ({r['times']}×)" if r.get('times', 0) > 1 else ''))
        return
    if args[0] != 'add' or len(args) != 6:
        sys.exit(__doc__)
    _, ident, name, price, qty, effect = args
    kind, _, value = effect.partition(':')
    if kind not in ('pantry', 'possession') or not value:
        sys.exit('Effect must be pantry:N or possession:NAME.')
    path = ROOT / 'crow-stock-orders.json'
    orders = json.loads(path.read_text()) if path.exists() else []
    orders.append({'id': ident, 'name': name, 'price': float(price), 'qty': int(qty), 'effect': effect})
    path.write_text(json.dumps(orders, indent=2))
    print(f'Queued: {qty} × {name} at {price} credit. It arrives at the trading post within about 15 seconds while Crow runs.')


if __name__ == '__main__':
    main()
