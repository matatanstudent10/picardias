#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rehace la lencería BAJO PEDIDO (catálogo "catalogo lenceria picardias.pdf") a partir de
una TABLA revisada a mano página por página (más fiable que adivinar con regex).
Fotos: cada producto toma las imágenes de su(s) página(s); en páginas con dos productos
(pantys, ligas) se reparten por mitad superior/inferior. Variantes de precio (con/sin
liguero, etc.) son productos aparte que comparten las fotos del producto base.

Borra antes los .md (y sus carpetas de fotos) de códigos NO numéricos: la lencería del
catálogo principal (248-291) es numérica y no se toca. Luego correr compilar.py.

Uso: python3 scripts/rehacer_lenceria.py "<pdf lenceria>"
"""
import sys, os, io, shutil
import pymupdf
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD_DIR = os.path.join(PROJ, "content", "productos")
IMG_DIR = os.path.join(PROJ, "public", "img")
MITAD = 506  # alto visible de página ~1013 pt

T = "Tallas: "
# (páginas, código, nombre, precio, descripción, [variantes (sufijo, nombre, precio)])
# páginas: "12" | "139a" (mitad superior) | "139b" (mitad inferior)
TABLA = [
    ("3", "set-1012", "Set 1012", 110000, T + "32-34-36"),
    ("4", "conjunto-8668", "Conjunto 8668 sin ligueros", 87500, T + "32-34-36-38",
        [("con-ligueros", "Conjunto 8668 con ligueros", 107700)]),
    ("5", "conjunto-8566", "Conjunto 8566 sin ligueros", 88700, T + "32-34-36-38",
        [("con-ligueros", "Conjunto 8566 con ligueros", 108700)]),
    ("6", "corset-8074", "Corset 85 8074", 119000, T + "32-34-36"),
    ("7", "conjunto-8531", "Conjunto 8531", 102000, T + "32-34-36-38"),
    ("8", "babydoll-484", "Babydoll 484", 95000, T + "32-34-36-38"),
    ("9", "babydoll-8483", "Babydoll 8483", 85000, T + "32-34-36-38"),
    ("10", "babydoll-8071", "Babydoll 8071", 117000, T + "32-36-38"),
    ("11", "conjunto-8528", "Conjunto 8528", 105900, T + "32-34-36-38"),
    ("12", "corset-8558", "Corset 8558", 121000, T + "32-34-36-38"),
    ("13", "conjunto-80539", "Conjunto 80539 completo", 95000, T + "32-34-36-38",
        [("sin-liguero", "Conjunto 80539 sin liguero", 70500)]),
    ("14", "conjunto-1994", "Conjunto 1994", 105000, T + "32-34-36-38"),
    ("15", "conjunto-1998", "Conjunto 1998", 105000, T + "32-34-36-38"),
    ("16", "conjunto-1998-m2", "Conjunto 1998 modelo 2", 98000, T + "32-34-36-38",
        [("con-liguero", "Conjunto 1998 modelo 2 con liguero", 120000)]),
    ("17", "corset-8556", "Corset 8556", 93000, T + "32-34-36"),
    ("18", "corset-erotico-8538", "Corset erótico 8538", 120000, T + "32-34-36-38"),
    ("19", "conjunto-80542", "Conjunto 80542 completo", 95000, T + "32-34-36-38",
        [("sin-liguero", "Conjunto 80542 sin liguero", 70500)]),
    ("20", "corset-blonda-8006", "Corset blonda 8006", 105500, T + "32-34-36-38"),
    ("21,22", "conjunto-80555", "Conjunto 80555", 94000, T + "S-M-L-XL"),
    ("21", "conjunto-80555-liguero-aros", "Conjunto 80555 + liguero aros", 115000, T + "S-M-L-XL"),
    ("22", "conjunto-80555-liguero-cadena", "Conjunto 80555 + liguero cadena", 115000, T + "S-M-L-XL"),
    ("23", "conjunto-80540", "Conjunto 80540 solo cadena", 93600, T + "32-34-36-38",
        [("completo", "Conjunto 80540 completo", 117300)]),
    ("24", "set-liguero-80543", "Set liguero 80543", 65000, T + "S-M-L"),
    ("25", "conjunto-print-85550", "Conjunto print 85550", 85000, T + "32-34-36-38"),
    ("26", "conjunto-copa-80544", "Conjunto copa 80544", 78000, T + "S-M-L-XL"),
    ("27", "set-valentin-8049", "Set Valentín 8049", 89000, T + "32-34-36"),
    ("28", "set-150427", "Set 150427", 55000, "Talla única. Incluye corbatica"),
    ("29", "conjunto-deportivo", "Conjunto deportivo", 39000, T + "M-L-XL"),
    ("31", "babydoll-1513", "Babydoll 1513", 90000, T + "32-34-36"),
    ("32", "babydoll-8052", "Babydoll 8052", 97800, T + "32-34-36"),
    ("33", "babydoll-2135", "Babydoll 2135 funcional", 117000, T + "32-34-36"),
    ("34", "babydoll-808", "Babydoll 808", 125000, T + "32-34-36-38"),
    ("35", "babydoll-2018", "Babydoll 2018", 122300, T + "32-34-36-38"),
    ("36", "babydoll-2045", "Babydoll 2045", 121500, T + "32-34-36-38"),
    ("37", "babydoll-820", "Babydoll 820", 121500, T + "32-34-36-38"),
    ("38", "babydoll-2013", "Babydoll 2013", 92300, T + "32-34-36-38"),
    ("39", "babydoll-8025", "Babydoll 8025", 121500, "Talla: 36"),
    ("40", "babydoll-4117", "Babydoll 4117", 98000, T + "32-34-36"),
    ("41", "babydoll-4128", "Babydoll 4128", 115000, T + "32-34-36"),
    ("42", "babydoll-4127", "Babydoll 4127", 75000, T + "32-34-36-38"),
    ("43", "babydoll-8012", "Babydoll 8012", 95500, "Talla: 32"),
    ("44", "babydoll-8015", "Babydoll 8015", 101500, T + "32-34-36"),
    ("45", "babydoll-813", "Babydoll 813", 115000, T + "32-34-36-38"),
    ("46", "babydoll-2087", "Babydoll 2087", 70000, T + "32-36-38"),
    ("48", "corpino-8601", "Corpiño 8601", 109000, T + "32-34-36"),
    ("49", "corset-814", "Corset 814", 121000, T + "32-36-38"),
    ("50", "corset-2014", "Corset 2014", 121000, T + "32-34-36-38"),
    ("51", "corset-2048", "Corset 2048", 121000, T + "32-34-36-38"),
    ("52", "conjunto-7735", "Conjunto 7735", 90000, T + "32-34-36-38"),
    ("53", "body-8625", "Body 8625", 110500, T + "32-36"),
    ("54", "body-7702", "Body 7702", 85000, T + "32-34-36-38"),
    ("56", "conjunto-8911", "Conjunto 8911", 89000, T + "32-34-36-38"),
    ("57", "conjunto-80101", "Conjunto 80101", 60000, T + "32-34-36"),
    ("58", "conjunto-lycra-80549", "Conjunto lycra 80549", 70000, T + "S-M-L-XL"),
    ("59", "conjunto-80103", "Conjunto 80103", 70000, T + "32-34-36-38"),
    ("60", "conjunto-4113", "Conjunto 4113", 50000, T + "32-34-36"),
    ("61", "conjunto-1999", "Conjunto 1999", 98000, T + "34-38"),
    ("62", "conjunto-8038", "Conjunto 8038", 85000, T + "32-36-38"),
    ("63", "conjunto-4108", "Conjunto 4108", 65000, T + "32-34-36"),
    ("65", "trio-olimpico-8602", "Trío olímpico 8602", 95000, T + "32-34-36-38",
        [("con-liguero", "Trío olímpico 8602 con liguero", 117000)]),
    ("66", "set-erotico-15360", "Set erótico 15360", 55000, T + "S/M - L/XL"),
    ("67", "set-15855", "Set 15855", 54000, "Talla única"),
    ("68", "conjunto-8046", "Conjunto 8046", 95000, T + "32-34-36"),
    ("69", "set-1015", "Set 1015", 101500, T + "32-34-36"),
    ("70", "set-15305", "Set 15305", 50000, "Talla única"),
    ("71", "set-15306", "Set 15306", 50000, "Talla única"),
    ("72", "trio-erotico-4360", "Trío erótico 4360", 65000, "Talla única"),
    ("73", "set-erotico-8070", "Set erótico 8070", 106000, T + "32-34-36-38"),
    ("74", "set-8047", "Set 8047", 89000, T + "S-M-L"),
    ("75", "set-8654", "Set 8654", 105000, "Talla: 36"),
    ("76", "babydoll-4115", "Babydoll 4115", 105300, T + "32-34-36-38"),
    ("77", "babydoll-8060", "Babydoll 8060", 120000, T + "32-36-38. No incluye medias"),
    ("78", "pijama-8023", "Pijama 8023", 92300, T + "32-34-36-38"),
    ("79", "babydoll-8090", "Babydoll 8090", 65000, T + "30-32-34-36. Incluye ligueros y ligas"),
    ("80", "mucama-1544", "Disfraz mucama 1544", 50000, "Talla única"),
    ("81", "trikini-605", "Trikini 605", 102000, T + "32-34-36-38"),
    ("82", "set-erotico-2071", "Set erótico 2071", 119000, T + "32-34-36-38"),
    ("83", "set-erotico-15090", "Set erótico 15090", 90000, T + "S-M-L. Incluye ligas y ligueros, no incluye medias"),
    ("84", "set-erotico-15091", "Set erótico 15091", 90000, T + "S-M-L. Incluye ligas y ligueros"),
    ("85", "set-erotico-8002", "Set erótico 8002 sin accesorios", 85000, "Talla: 38",
        [("con-accesorios", "Set erótico 8002 con accesorios", 115800)]),
    ("87a", "ligas-051", "Ligas 051", 12000, "Talla única"),
    ("87b", "ligas-060", "Ligas 060", 12000, "Talla única"),
    ("88a", "ligas-057", "Ligas 057", 12000, "Talla única"),
    ("88b", "ligas-055", "Ligas 055", 12000, "Talla única"),
    ("89", "liguero-059", "Liguero 059", 30000, "Talla única. No incluye ligas ni panty"),
    ("90", "liguero-075", "Liguero 075", 30000, "Talla única. No incluye medias ni panty"),
    ("91", "liguero-095", "Liguero 095", 37000, "Talla única. No incluye panty"),
    ("92", "liguero-097", "Liguero 097", 42000, "Talla única. No incluye panty"),
    ("93", "liguero-098", "Liguero 098", 45000, "Talla única. No incluye panty"),
    ("94", "liguero-077", "Liguero 077", 30000, "Talla única. No incluye medias ni panty"),
    ("95", "liguero-8002-3", "Liguero 8002-3", 28000, "Talla única. No incluye ligas ni panty"),
    ("96", "corbatica-9999", "Corbatica 9999", 25000, "Talla única. No incluye top"),
    ("97", "bralette-067", "Bralette 067", 28000, "Talla única"),
    ("98", "medias-003", "Medias 003", 30000, "Talla única"),
    ("99", "medias-maya", "Medias maya", 30000, "Talla única"),
    ("100", "medias-pantalon", "Medias pantalón", 30000, "Talla única"),
    ("101,102", "medias-088", "Medias 088", 30000, T + "S-M / L-XL"),
    ("103", "guantes-216", "Guantes 216", 22000, ""),
    ("104", "kimono-810", "Kimono 810", 85000, T + "32-34-36. No incluye panty ni top"),
    ("105", "kimono-812", "Kimono 812", 90000, T + "M-L"),
    ("106", "monja-sexy-15041", "Disfraz monja sexy 15041", 45000, T + "S-M / L-XL"),
    # Tallas plus
    ("108", "body-7719", "Body 7719 (talla plus)", 89000, T + "38-40-42-44"),
    ("109", "body-2058", "Body 2058 (talla plus)", 45000, T + "38-40-42-44"),
    ("110", "set-86108", "Set 86108 (talla plus)", 135000, T + "38-40-42-44"),
    ("111", "babydoll-64106", "Babydoll 64106 (talla plus)", 128000, T + "38-40-42-44"),
    ("112", "conjunto-7717-1", "Conjunto 7717-1 (talla plus)", 80000, T + "38-40-42"),
    ("113", "conjunto-7704-1", "Conjunto 7704-1 (talla plus)", 80000, T + "38-40-42"),
    ("114", "conjunto-8092", "Conjunto 8092 (talla plus)", 80000, "Talla: 38"),
    ("115", "conjunto-64103", "Conjunto 64103 (talla plus)", 89000, T + "38-40-42-44"),
    ("116", "set-64102", "Set 64102 (talla plus)", 95000, T + "38-40-42-44. No incluye kimono"),
    ("117", "tanga-71157", "Tanga 71157 (talla plus)", 20000, T + "XL-2XL-3XL-4XL"),
    ("118", "tanga-71156", "Tanga 71156 (talla plus)", 20000, T + "38-40-42-44"),
    # La'Ragazza
    ("120", "laragazza-15315", "Set La'Ragazza 15315", 25000, "Talla única"),
    ("121", "laragazza-15313", "Set La'Ragazza 15313", 25000, "Talla única"),
    ("122", "laragazza-15319", "Set La'Ragazza 15319", 55000, T + "32-34-36-38"),
    ("123", "laragazza-15321", "Set La'Ragazza 15321", 55000, T + "32-34-36-38"),
    ("124", "laragazza-15351", "Set La'Ragazza 15351", 55000, T + "32-34-36-38"),
    ("125", "laragazza-15704", "Set La'Ragazza 15704", 58000, T + "S/M - L/XL"),
    ("126", "laragazza-15706", "Set La'Ragazza 15706", 58000, T + "S/M - L/XL"),
    ("127", "laragazza-15316", "Set La'Ragazza 15316", 30000, "Talla única"),
    ("128", "laragazza-15310", "Disfraz mucama La'Ragazza 15310", 30000, "Talla única"),
    ("129", "laragazza-15307", "Set La'Ragazza 15307", 38800, "Talla única"),
    ("130", "laragazza-15312", "Set La'Ragazza 15312", 38600, "Talla única"),
    ("131", "laragazza-15029", "Set La'Ragazza 15029", 45000, "Talla única"),
    ("132", "laragazza-15026", "Set La'Ragazza 15026", 40000, "Talla única"),
    ("133", "laragazza-15025", "Set La'Ragazza 15025", 29500, "Talla única"),
    ("134", "laragazza-15001", "Set La'Ragazza 15001", 54000, "Talla única"),
    ("135", "laragazza-15028", "Set La'Ragazza 15028", 39000, "Talla única"),
    # Pantys (dos por página)
    ("137a,138b", "panty-77156", "Panty lycra 77156", 18000, T + "S-M-L-XL"),
    ("137b", "panty-77157", "Panty lycra y encaje 77157", 18000, T + "S-M-L-XL"),
    ("138a", "cachetero-1040", "Cachetero encaje 1040", 15000, T + "S-M-L-XL"),
    ("139a", "panty-379", "Panty 379", 16200, "Talla única. Varios tonos"),
    ("139b", "panty-907", "Panty 907", 14200, "Talla única. Varios tonos"),
    ("140a", "panty-426", "Panty 426", 34000, "Talla única. Varios tonos"),
    ("140b", "panty-417", "Panty 417", 16500, "Talla única. Varios tonos"),
    ("141a", "panty-427", "Panty 427", 27900, "Talla única. Varios tonos"),
    ("141b", "panty-407", "Panty 407", 17300, T + "M-L. Varios tonos"),
    ("142a", "panty-315", "Panty 315", 16900, "Talla única. Blanco, negro, rojo"),
    ("142b", "panty-1016", "Panty 1016", 18000, T + "S-M-L-XL. Varios tonos"),
    ("143a", "panty-119", "Panty 119", 15000, "Talla única. Blanco, negro, rojo, palo de rosa, vino, azul"),
    ("143b", "panty-121", "Panty 121", 16000, "Talla única. Vino, azul, blanco"),
    ("144a", "panty-378", "Panty 378", 16000, "Talla única. Varios tonos"),
    ("144b", "panty-333", "Panty 333", 13000, "Talla única. Varios tonos"),
    ("145a", "panty-313", "Panty 313", 16000, "Talla única. Varios tonos"),
    ("145b", "panty-904", "Panty 904", 14500, "Talla única. Varios tonos"),
    ("146a", "panty-133", "Panty 133", 18000, "Talla única. Varios tonos"),
    ("146b", "panty-132", "Panty 132", 19500, "Talla única. Varios tonos"),
    ("147a", "panty-344", "Panty 344 animal print", 15000, "Talla única"),
    ("147b", "panty-128", "Panty 128", 14700, "Talla única. Varios tonos"),
    ("148a", "panty-150", "Panty 150", 16200, "Talla única. Varios tonos"),
    ("148b", "panty-136", "Panty 136", 12000, "Talla única. Varios tonos"),
    ("149a", "panty-331", "Panty 331", 12000, "Talla única. Varios tonos"),
    ("149b", "panty-122", "Panty 122", 16000, "Talla única. Varios tonos"),
    ("150a", "panty-1353", "Panty 1353", 14900, T + "S-M-L-XL. Varios tonos"),
    ("150b", "panty-1352", "Panty 1352", 14900, T + "S/M - L/XL. Varios tonos"),
    # Lencería para hombre
    ("152", "hombre-15057", "Lencería hombre 15057", 30000, "Talla única"),
    ("153", "hombre-15055", "Lencería hombre 15055", 30000, "Talla única"),
    ("154", "hombre-15053", "Lencería hombre 15053", 30000, "Talla única"),
    ("155", "hombre-15060", "Lencería hombre 15060", 30000, T + "S-M-L"),
    ("156", "hombre-15061", "Lencería hombre 15061", 30000, T + "S-M-L"),
    ("157", "hombre-15058", "Lencería hombre 15058", 30000, T + "S-M-L"),
    ("158", "hombre-15051", "Lencería hombre 15051", 30000, "Talla única"),
    ("159", "hombre-15063", "Lencería hombre 15063", 35000, T + "S-M-L"),
]


def imagenes_de(doc, spec):
    """xrefs de las fotos de una página (o media página), la más grande primero."""
    pg, mitad = (int(spec[:-1]), spec[-1]) if spec[-1] in "ab" else (int(spec), None)
    page = doc[pg - 1]
    out, seen = [], set()
    infos = page.get_image_info(xrefs=True)          # en orden de dibujo
    def tapada(k):                                    # otra imagen posterior la cubre entera
        a = infos[k]["bbox"]
        return any(b["bbox"][0] <= a[0] + 3 and b["bbox"][1] <= a[1] + 3 and
                   b["bbox"][2] >= a[2] - 3 and b["bbox"][3] >= a[3] - 3
                   for b in infos[k + 1:] if b["xref"] != infos[k]["xref"])
    for k, im in enumerate(infos):
        if tapada(k): continue
        x0, y0, x1, y1 = im["bbox"]
        w, h = x1 - x0, y1 - y0
        if min(w, h) < 60 or im["xref"] in seen or im["width"] < 50:
            continue          # muestras de color, logos, flechas
        cy = (y0 + y1) / 2
        if mitad == "a" and cy >= MITAD: continue
        if mitad == "b" and cy < MITAD: continue
        seen.add(im["xref"]); out.append((w * h, im["xref"]))
    return [x for _, x in sorted(out, reverse=True)]


# Huella (16x16, sobre el promedio) de la imagen de relleno "cielo con nube" que el PDF
# esconde detrás de algunas fotos; se descarta.
RELLENO = "1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100000111111111110000000000001111000000000000000000000000000000000000000000000000"

def huella(img):
    g = img.convert("L").resize((16, 16)); px = list(g.get_flattened_data()); m = sum(px) / len(px)
    return "".join("1" if p > m else "0" for p in px)


def es_relleno(img):
    bits = huella(img)
    if sum(a != b for a, b in zip(bits, RELLENO)) > 12: return False
    r, gr, b = img.convert("RGB").resize((1, 1)).getpixel((0, 0))
    return gr >= r and gr >= b   # cielo + pasto: domina el verde (evita falsos positivos)


def guardar(doc, xref, dest, vistas, box=900):
    """Guarda la foto como WebP; False si es relleno o repite otra foto del producto."""
    info = doc.extract_image(xref)
    img = Image.open(io.BytesIO(info["image"]))
    if info.get("smask"):
        mask = Image.open(io.BytesIO(doc.extract_image(info["smask"])["image"])).convert("L")
        img = img.convert("RGB"); img.putalpha(mask.resize(img.size))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA"); fondo = Image.new("RGB", img.size, "white")
        fondo.paste(img, mask=img.split()[-1]); img = fondo
    img = img.convert("RGB")
    if es_relleno(img): return False
    h = huella(img)
    if any(sum(a != b for a, b in zip(h, v)) <= 6 for v in vistas): return False
    vistas.append(h)
    img.thumbnail((box, box))
    img.save(dest, "WEBP", quality=80, method=6)
    return True


def md(codigo, nombre, precio, imgs, desc):
    lineas = ["---", f'codigo: "{codigo}"', f'nombre: "{nombre}"', f"precio: {precio}",
              "categoria: lenceria", "imagenes:"] + [f"  - {i}" for i in imgs] + \
             [f'descripcion: "{desc}"', "activo: true", "bajo_pedido: true", "---", ""]
    with open(os.path.join(PROD_DIR, codigo + ".md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))


def main():
    doc = pymupdf.open(sys.argv[1])
    # 1) borrar la lencería bajo pedido anterior (códigos no numéricos)
    borrados = 0
    for fn in os.listdir(PROD_DIR):
        c = fn[:-3]
        if fn.endswith(".md") and not c.isdigit():
            os.remove(os.path.join(PROD_DIR, fn)); borrados += 1
            d = os.path.join(IMG_DIR, c)
            if os.path.isdir(d) and not c.startswith("_") and c != "uploads":
                shutil.rmtree(d)
    # 2) generar desde la tabla
    total, sin_foto = 0, []
    for fila in TABLA:
        specs, codigo, nombre, precio, desc = fila[:5]
        variantes = fila[5] if len(fila) > 5 else []
        xrefs = []
        for s in specs.split(","):
            xrefs += [x for x in imagenes_de(doc, s) if x not in xrefs]
        os.makedirs(os.path.join(IMG_DIR, codigo), exist_ok=True)
        rutas, vistas = [], []
        for x in xrefs:
            n = len(rutas) + 1
            if guardar(doc, x, os.path.join(IMG_DIR, codigo, f"{n}.webp"), vistas):
                rutas.append(f"public/img/{codigo}/{n}.webp")
        if not rutas: sin_foto.append(codigo)
        md(codigo, nombre, precio, rutas, desc); total += 1
        for suf, vnom, vprecio in variantes:     # comparten fotos del producto base
            md(f"{codigo}-{suf}", vnom, vprecio, rutas, desc); total += 1
    print(f"Borrados {borrados} .md anteriores; generados {total} productos de lencería.")
    if sin_foto: print("SIN FOTO:", ", ".join(sin_foto))


if __name__ == "__main__":
    main()
