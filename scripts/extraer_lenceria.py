#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae el catálogo de LENCERÍA (bajo pedido) a content/productos + public/img.
Formato distinto al principal: productos por REFERENCIA (ej. "CONJUNTO 8668"),
tallas y precio. Se marca bajo_pedido: true. Best-effort -> revisar en el admin.

Uso: python3 scripts/extraer_lenceria.py "<pdf_lenceria>"
"""
import sys, os, re, io, unicodedata
import pymupdf
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD_DIR = os.path.join(PROJ, "content", "productos")

TIPOS = r"(?:SET|CONJUNTO|CORSET|BODY|BODYSUIT|BABYDOLL|BRALETTE|TANGA|BRASIER|BRASSIER|LIGUERO|BATA|KIMONO|PICARDIA|PICARDÍA|VESTIDO|DISFRAZ|MEDIA[S]?|PANTY|BODYS|ARNES|ARNÉS)"
REF_RE = re.compile(rf"({TIPOS}[\s\w]*?\d{{2,5}})", re.I)
PRICE_RE = re.compile(r"\$\s*([\d][\d.\, ]*\d)")
SIZE_RE = re.compile(r"\b(\d{2}(?:\s*-\s*\d{2}){1,4})\b")

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def titlecase_ref(s):
    return re.sub(r"\s+", " ", s.strip()).title()

def imgs_pagina(page):
    out, seen = [], set()
    for im in page.get_images(full=True):
        x = im[0]
        if x in seen: continue
        rs = page.get_image_rects(x)
        if not rs: continue
        r = rs[0]
        if not (120 <= r.width <= 900 and 120 <= r.height <= 1000): continue
        seen.add(x); out.append((round(r.y0 / 40), r.x0, x))
    out.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in out]

def save_webp(doc, xref, dest, box=900):
    info = doc.extract_image(xref)
    img = Image.open(io.BytesIO(info["image"])).convert("RGB")
    img.thumbnail((box, box))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest, "WEBP", quality=80, method=6)

def parse_precio(s):
    raw = re.sub(r"[^\d]", "", s)
    return int(raw) if raw else 0

def main():
    pdf = sys.argv[1]
    doc = pymupdf.open(pdf)
    productos = {}   # code -> dict
    orden = []
    ultimo = None    # última referencia creada (para adjuntar fotos huérfanas)
    for i in range(doc.page_count):
        page = doc[i]
        txt = page.get_text()
        # referencias únicas en orden de aparición
        refs = []
        for m in REF_RE.finditer(txt):
            r = re.sub(r"\s+", " ", m.group(1).strip())
            if r not in refs: refs.append(r)
        precios = [parse_precio(p) for p in PRICE_RE.findall(txt)]
        precios = [p for p in precios if 5000 <= p <= 2000000]
        tallas = SIZE_RE.findall(txt)
        xs = imgs_pagina(page)
        if not xs:
            continue
        if not refs:
            # sin referencia: adjunta las fotos al último producto (más vistas del mismo)
            if ultimo and len(productos[ultimo]["imagenes"]) < 6:
                base = len(productos[ultimo]["imagenes"])
                for k, x in enumerate(xs):
                    dest = f"public/img/{ultimo}/{base+k+1}.webp"
                    try: save_webp(doc, x, os.path.join(PROJ, dest)); productos[ultimo]["imagenes"].append(dest)
                    except Exception: pass
            continue
        # repartir imágenes entre las referencias de la página, en orden
        per = max(1, len(xs) // len(refs))
        for idx, ref in enumerate(refs):
            code = slug(ref)
            if code in productos:                      # misma ref en otra página: suma fotos
                pass
            start = idx * per
            fin = start + per if idx < len(refs) - 1 else len(xs)
            imgs_ref = xs[start:fin]
            rutas = []
            for k, x in enumerate(imgs_ref):
                dest = f"public/img/{code}/{k+1 if code not in productos else len(productos[code]['imagenes'])+k+1}.webp"
                try: save_webp(doc, x, os.path.join(PROJ, dest)); rutas.append(dest)
                except Exception: pass
            precio = precios[idx] if idx < len(precios) else (precios[0] if precios else 0)
            talla = tallas[0] if tallas else ""
            desc = f"Tallas: {talla}" if talla else ""
            if code in productos:
                productos[code]["imagenes"] += rutas
            else:
                productos[code] = {"codigo": code, "nombre": titlecase_ref(ref),
                    "precio": precio, "categoria": "lenceria", "imagenes": rutas,
                    "descripcion": desc, "bajo_pedido": True}
                orden.append(code)
            ultimo = code

    # escribir md
    os.makedirs(PROD_DIR, exist_ok=True)
    for code in orden:
        p = productos[code]
        fm = (f"---\ncodigo: \"{p['codigo']}\"\nnombre: \"{p['nombre'].replace(chr(34),'')}\"\n"
              f"precio: {p['precio']}\ncategoria: lenceria\nimagenes:\n")
        for im in p["imagenes"]: fm += f"  - {im}\n"
        fm += f"descripcion: \"{p['descripcion']}\"\nactivo: true\nbajo_pedido: true\n---\n"
        with open(os.path.join(PROD_DIR, f"{p['codigo']}.md"), "w", encoding="utf-8") as f:
            f.write(fm)

    con_precio = sum(1 for c in orden if productos[c]["precio"])
    genericos = sum(1 for c in orden if productos[c]["nombre"].startswith("Lencería (ref"))
    print(f"Lencería: {len(orden)} productos | con precio: {con_precio} | genéricos sin ref: {genericos}")

if __name__ == "__main__":
    main()
