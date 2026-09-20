#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reasigna la categoría de los productos NUMÉRICOS por RANGO de código, usando la
página donde aparece cada encabezado de sección en el PDF. Más robusto que el
"último encabezado visto" (que sangra categorías por el desorden del texto).
No toca la lencería (códigos no numéricos). Luego hay que correr compilar.py.

Uso: python3 scripts/recategorizar.py "<pdf principal>"
"""
import sys, os, re, pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraer_catalogo as E

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD_DIR = os.path.join(PROJ, "content", "productos")
CODE = re.compile(r"^(\d{1,3})\s*[-–]")

def construir_rangos(doc):
    events = []
    for i in range(doc.page_count):
        lines = [l.strip() for l in doc[i].get_text().splitlines()]
        heads = [h for h in (E.match_cat(l) for l in lines) if h]
        codes = sorted({int(m.group(1)) for l in lines for m in [CODE.match(l)]
                        if m and 1 <= int(m.group(1)) <= 450})
        events.append((heads, codes))
    ranges = []
    for idx, (heads, codes) in enumerate(events):
        if len(heads) > 2 or not heads:   # salta TOC y páginas sin encabezado
            continue
        sc = codes[0] if codes else None
        k = idx
        while sc is None and k + 1 < len(events):
            k += 1
            sc = events[k][1][0] if events[k][1] else None
        if sc is not None:
            ranges.append((sc, heads[0]))
    ranges.sort()
    return ranges

def cat_de(c, ranges):
    r = "otros"
    for sc, slug in ranges:
        if c >= sc: r = slug
        else: break
    return r

def main():
    doc = pymupdf.open(sys.argv[1])
    ranges = construir_rangos(doc)
    cambios = 0
    for fn in os.listdir(PROD_DIR):
        base = fn[:-3]
        if not (fn.endswith(".md") and base.isdigit()):
            continue
        ruta = os.path.join(PROD_DIR, fn)
        txt = open(ruta, encoding="utf-8").read()
        nueva = cat_de(int(base), ranges)
        m = re.search(r"^categoria:\s*(.+)$", txt, re.M)
        if m and m.group(1).strip() != nueva:
            txt = re.sub(r"^categoria:.*$", f"categoria: {nueva}", txt, count=1, flags=re.M)
            open(ruta, "w", encoding="utf-8").write(txt)
            cambios += 1
    print(f"Recategorizados {cambios} productos numéricos.")

if __name__ == "__main__":
    main()
