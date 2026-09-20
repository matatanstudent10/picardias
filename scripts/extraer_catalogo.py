#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae el catálogo de Picardías (PDF) a datos + imágenes para el sitio.

Enfoque (tras analizar el PDF):
  - NOMBRE/PRECIO/CATEGORÍA: parseo LINEAL del texto (orden de lectura), que sale
    limpio (~249 productos, ~99% con precio). Códigos válidos 1..250.
  - IMÁGENES: por página de producto, se ordenan las fotos por posición (grilla) y
    se emparejan con los códigos de esa página en orden ascendente. Es un
    EMPAREJAMIENTO ESTIMADO -> requiere repaso en el admin.
  - El PDF tiene una fuente con acentos rotos (�). Se corrige con un diccionario;
    lo que quede con � se reporta para arreglo manual.

Salidas:
  public/products.json         (categorias + productos)
  public/img/<codigo>/1.webp   (foto principal estimada)
  public/img/_pool/pXX_YY.webp (todas las fotos, para repicar en el admin)
  content/productos/<codigo>.md

Uso: python3 scripts/extraer_catalogo.py "<pdf>"
"""
import sys, os, re, json, io, unicodedata
import pymupdf
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(PROJ, "public", "img")
POOL = os.path.join(IMG, "_pool")
PROD_DIR = os.path.join(PROJ, "content", "productos")
JSON_OUT = os.path.join(PROJ, "public", "products.json")

# Orden y etiqueta visible de cada categoría (según el catálogo)
CAT_ORDER = [
    ("lubricantes-calientes", "Lubricantes Calientes"),
    ("electrizantes", "Lubricantes Electrizantes"),
    ("frio-caliente", "Frío - Caliente"),
    ("multiorgasmo", "Lubricantes Multiorgasmo"),
    ("anales-retardantes", "Anales Retardantes"),
    ("estrechantes", "Estrechantes"),
    ("potenciadores", "Potenciadores"),
    ("para-masajes", "Para Masajes"),
    ("kits", "Kits"),
    ("feromonas", "Feromonas"),
    ("juegos", "Juegos"),
    ("anillos-fundas", "Anillos - Fundas"),
    ("balas-huevos", "Balas - Huevos"),
    ("arnes-sado", "Arnés - Sado"),
    ("lenceria", "Lencería"),
    ("plug-anal", "Plug Anal"),
    ("masturbadores", "Masturbadores"),
    ("masajeadores", "Masajeadores"),
    ("vibradores-con-pila", "Vibradores con Pila"),
    ("vibradores-clitoris", "Vibradores Clítoris"),
    ("vibradores-con-app", "Vibradores con App"),
    ("succionadores", "Succionadores"),
    ("otros", "Otros"),
]
CAT_LABEL = dict(CAT_ORDER)
# Encabezados EXACTOS tal como aparecen (normalizados) -> slug. Más específico primero.
HEADERS = [
    ("vibradores con app", "vibradores-con-app"),
    ("vibradores con pila", "vibradores-con-pila"),
    ("lubricantes electrizantes", "electrizantes"),
    ("lubricantes multiorgasmo", "multiorgasmo"),
    ("lubricantes frio- caliente", "frio-caliente"),
    ("lubricantes frio caliente", "frio-caliente"),
    ("lubricantes calientes", "lubricantes-calientes"),
    ("lubricantes anales", "anales-retardantes"),
    ("anillos-fundas", "anillos-fundas"),
    ("anillos - fundas", "anillos-fundas"),
    ("balas - huevos", "balas-huevos"),
    ("balas huevos", "balas-huevos"),
    ("arnes - sado", "arnes-sado"),
    ("arnes sado", "arnes-sado"),
    ("plug anal", "plug-anal"),
    ("masturbadoras", "masturbadores"),
    ("masturbadores", "masturbadores"),
    ("masajeadores", "masajeadores"),
    ("succionadores", "succionadores"),
    ("retardantes", "anales-retardantes"),
    ("estrechantes", "estrechantes"),
    ("potenciadoress", "potenciadores"),
    ("potenciadores", "potenciadores"),
    ("para masajes", "para-masajes"),
    ("feromonas", "feromonas"),
    ("lenceria", "lenceria"),
    ("juegos", "juegos"),
    ("kits", "kits"),
    ("vibradores", "vibradores-clitoris"),
    ("otros", "otros"),
]

# correcciones de acentos rotos (�) frecuentes en este catálogo
FIX = {
    "coraz�n": "corazón", "lim�n": "limón", "algod�n": "algodón",
    "maracuy�": "maracuyá", "vibraci�n": "vibración", "estimulaci�n": "estimulación",
    "an�s": "anís", "cl�toris": "clítoris", "cl�torise": "clítoris", "ba�o": "baño",
    "ba�os": "baños", "tama�o": "tamaño", "peque�o": "pequeño", "compa�ero": "compañero",
    "dise�o": "diseño", "�": "",
}

def fix_txt(s):
    for a, b in FIX.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()

def match_cat(linea):
    if "$" in linea or re.search(r"\d", linea):
        return None
    n = norm(linea)
    if not (3 <= len(n) <= 30):
        return None
    for frase, slug in HEADERS:
        if frase in n:
            return slug
    return None

CODE = re.compile(r"^(\d{1,3})\s*[-–]\s*(.*)$")
PRICE = re.compile(r"\$\s*([\d][\d.,]*)")

def parse_lineal(doc):
    """Devuelve {codigo:int -> (nombre, precio_int, categoria)}."""
    full = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    lines = [l.strip() for l in full.splitlines()]
    prods = {}
    cat = "otros"
    i = 0
    while i < len(lines):
        c = match_cat(lines[i])
        if c:
            cat = c; i += 1; continue
        m = CODE.match(lines[i])
        if m:
            cod = int(m.group(1)); rest = m.group(2); name = rest; price = None
            pm = PRICE.search(rest)
            if pm: price = pm.group(1); name = PRICE.sub("", rest)
            j = i + 1; look = 0
            while j < len(lines) and look < 3:
                if CODE.match(lines[j]) or match_cat(lines[j]): break
                pm = PRICE.search(lines[j])
                if pm and price is None: price = pm.group(1)
                frag = PRICE.sub("", lines[j]).strip()
                if frag and not frag.isdigit() and len(name) < 55:
                    name = (name + " " + frag).strip()
                j += 1; look += 1
            if 1 <= cod <= 450:
                name = fix_txt(name).strip(" -–")
                p = int(price.replace(".", "").replace(",", "")) if price else None
                if cod not in prods and len(name) >= 3:
                    prods[cod] = (name, p, cat)
            i = j
        else:
            i += 1
    return prods

def imgs_pagina(page):
    mid = page.rect.width / 2
    out = []
    seen = set()
    for im in page.get_images(full=True):
        x = im[0]
        if x in seen: continue
        rs = page.get_image_rects(x)
        if not rs: continue
        r = rs[0]
        if not (60 <= r.width <= 450 and 60 <= r.height <= 450): continue  # excluye banner 613x1076 y iconos
        seen.add(x)
        out.append((round(r.y0 / 40), r.x0, x))
    out.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in out]

def codes_pagina(page):
    codes = []
    for ln in page.get_text().splitlines():
        m = CODE.match(ln.strip())
        if m:
            c = int(m.group(1))
            if 1 <= c <= 450: codes.append(c)
    return sorted(set(codes))

def save_webp(doc, xref, dest, box=900, q=80):
    info = doc.extract_image(xref)
    img = Image.open(io.BytesIO(info["image"])).convert("RGB")
    img.thumbnail((box, box))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest, "WEBP", quality=q, method=6)

def main():
    pdf = sys.argv[1]
    doc = pymupdf.open(pdf)
    prods = parse_lineal(doc)

    # imágenes: por página de producto (>=4 fotos), zip codigos_asc <-> imgs_grid
    os.makedirs(POOL, exist_ok=True)
    img_de = {}   # codigo -> ruta rel
    for i in range(doc.page_count):
        page = doc[i]
        xs = imgs_pagina(page)
        if len(xs) < 1:   # portada / divisor / índice (sin fotos de producto)
            continue
        cs = codes_pagina(page)
        for k, x in enumerate(xs):
            pool_rel = f"public/img/_pool/p{i+1:02d}_{k+1:02d}.webp"
            try: save_webp(doc, x, os.path.join(PROJ, pool_rel), box=900)
            except Exception: continue
            if k < len(cs):
                cod = cs[k]
                dest = f"public/img/{cod:02d}/1.webp"
                try:
                    save_webp(doc, x, os.path.join(PROJ, dest), box=900)
                    img_de[cod] = dest
                except Exception: pass

    # ensamblar
    finales = []
    rotos = []
    for cod in sorted(prods):
        nombre, precio, cat = prods[cod]
        if "�" in nombre: rotos.append((cod, nombre))
        finales.append({
            "codigo": f"{cod:02d}", "nombre": nombre, "precio": precio or 0,
            "categoria": cat, "imagenes": [img_de[cod]] if cod in img_de else [],
            "descripcion": "", "activo": True,
        })

    usadas = {p["categoria"] for p in finales}
    cats = [{"slug": s, "nombre": CAT_LABEL[s]} for s, _ in CAT_ORDER if s in usadas]
    os.makedirs(os.path.dirname(JSON_OUT), exist_ok=True)
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({"categorias": cats, "productos": finales}, f, ensure_ascii=False, indent=2)

    os.makedirs(PROD_DIR, exist_ok=True)
    for p in finales:
        fm = (f"---\ncodigo: \"{p['codigo']}\"\nnombre: \"{p['nombre'].replace(chr(34), '')}\"\n"
              f"precio: {p['precio']}\ncategoria: {p['categoria']}\nimagenes:\n")
        for im in p["imagenes"]: fm += f"  - {im}\n"
        fm += f"descripcion: \"\"\nactivo: {'true' if p['activo'] else 'false'}\n---\n"
        with open(os.path.join(PROD_DIR, f"{p['codigo']}.md"), "w", encoding="utf-8") as f:
            f.write(fm)

    con_img = sum(1 for p in finales if p["imagenes"])
    con_precio = sum(1 for p in finales if p["precio"])
    print(f"Productos: {len(finales)} | con precio: {con_precio} | con imagen: {con_img}")
    print(f"Nombres con acento roto (revisar): {len(rotos)}")
    for c, n in rotos[:15]: print(f"   {c}: {n}")

if __name__ == "__main__":
    main()
