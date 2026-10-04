#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compila content/productos/*.md  ->  public/products.json
(lo corre el GitHub Action en cada commit; no requiere librerías externas)
"""
import os, re, json, hashlib

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD_DIR = os.path.join(PROJ, "content", "productos")
OUT = os.path.join(PROJ, "public", "products.json")

CAT_ORDER = [
    ("lubricantes-calientes", "Lubricantes Calientes"), ("electrizantes", "Lubricantes Electrizantes"),
    ("frio-caliente", "Frío - Caliente"),
    ("neutros-saborizados", "Lubricantes Neutros - Saborizados"), ("multiorgasmo", "Lubricantes Multiorgasmo"),
    ("anales", "Lubricantes Anales"), ("retardantes", "Retardantes"), ("estrechantes", "Estrechantes"),
    ("potenciadores", "Potenciadores"), ("para-masajes", "Para Masajes"), ("kits", "Kits"),
    ("feromonas", "Feromonas"), ("juegos", "Juegos"), ("anillos-fundas", "Anillos - Fundas"),
    ("balas-huevos", "Balas - Huevos"), ("arnes-sado", "Arnés - Sado"), ("lenceria", "Lencería"),
    ("plug-anal", "Plug Anal"), ("masturbadores", "Masturbadores"), ("masajeadores", "Masajeadores"),
    ("vibradores-con-pila", "Vibradores con Pila"), ("vibradores-clitoris", "Vibradores Clítoris"), ("vibradores", "Vibradores"),
    ("vibradores-con-app", "Vibradores con App"), ("succionadores", "Succionadores"), ("otros", "Otros"),
]
CAT_LABEL = dict(CAT_ORDER)

def parse_frontmatter(txt):
    m = re.match(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m: return {}
    data, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s*-\s+", line) and key:            # item de lista
            data.setdefault(key, []).append(line.strip()[1:].strip().strip('"'))
            continue
        mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not mm: continue
        key, val = mm.group(1), mm.group(2).strip()
        if val == "":                                       # empieza una lista
            data[key] = []
        else:
            data[key] = val.strip().strip('"')
    return data

_HASH_CACHE = {}

def con_version(ruta):
    """Cache-busting: añade ?v=<md5[:8]> si el archivo existe en disco (relativo a la raíz)."""
    limpia = ruta.split("?", 1)[0]
    abs_path = os.path.join(PROJ, *limpia.lstrip("/").split("/"))
    if not os.path.isfile(abs_path):
        return ruta
    if abs_path not in _HASH_CACHE:
        h = hashlib.md5()
        with open(abs_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        _HASH_CACHE[abs_path] = h.hexdigest()[:8]
    return f"{limpia}?v={_HASH_CACHE[abs_path]}"

def main():
    prods = []
    for fn in sorted(os.listdir(PROD_DIR)):
        if not fn.endswith(".md"): continue
        d = parse_frontmatter(open(os.path.join(PROD_DIR, fn), encoding="utf-8").read())
        if not d.get("codigo"): continue
        try: precio = int(str(d.get("precio", "0")).replace(".", "").replace(",", "") or 0)
        except ValueError: precio = 0
        activo = str(d.get("activo", "true")).lower() != "false"
        bajo_pedido = str(d.get("bajo_pedido", "false")).lower() == "true"
        destacado = str(d.get("destacado", "false")).lower() == "true"
        imagenes = d.get("imagenes", []) if isinstance(d.get("imagenes"), list) else []
        prods.append({
            "codigo": str(d["codigo"]), "nombre": d.get("nombre", ""), "precio": precio,
            "categoria": d.get("categoria", "otros"),
            "imagenes": [con_version(r) for r in imagenes],
            "descripcion": d.get("descripcion", ""), "activo": activo, "bajo_pedido": bajo_pedido,
            "destacado": destacado,
        })
    # numéricos (catálogo principal) primero y en orden; luego la lencería bajo pedido por código
    prods.sort(key=lambda p: (0, int(p["codigo"]), "") if p["codigo"].isdigit() else (1, 0, p["codigo"]))
    usadas = {p["categoria"] for p in prods}
    cats = [{"slug": s, "nombre": CAT_LABEL[s]} for s, _ in CAT_ORDER if s in usadas]
    # una categoría usada en un .md pero olvidada en CAT_ORDER igual se publica (al final)
    cats += [{"slug": s, "nombre": s.replace("-", " ").title()} for s in sorted(usadas - set(CAT_LABEL))]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"categorias": cats, "productos": prods}, f, ensure_ascii=False, indent=2)
    print(f"Compilados {len(prods)} productos en {len(cats)} categorías -> public/products.json")

if __name__ == "__main__":
    main()
