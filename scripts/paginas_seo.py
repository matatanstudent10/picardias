#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO estático (lo llama compilar.py; sin librerías externas):
  - c/<slug>/index.html  una página por categoría a partir de index.html (plantilla con marcadores
                         <!--SEO:...-->): título/descripcion propios, productos ya escritos en el HTML
                         (Google los lee sin ejecutar JS) y datos estructurados ItemList/Product.
                         La app (assets/app.js) la abre filtrada gracias a <body data-cat="...">.
  - index.html           rellena el bloque de enlaces a categorías del pie (enlazado interno).
  - sitemap.xml          home + categorías.
"""
import os, re, json, html, datetime

SITIO = "https://picardias.win"
ZONA = "Medellín"


def _bloque(s, nombre, contenido):
    """Reemplaza lo que hay entre <!--SEO:nombre--> y <!--/SEO:nombre-->."""
    pat = re.compile(r"(<!--SEO:%s-->).*?(<!--/SEO:%s-->)" % (nombre, nombre), re.S)
    assert pat.search(s), f"falta el marcador SEO:{nombre} en index.html"
    return pat.sub(lambda m: m.group(1) + contenido + m.group(2), s, count=1)


def _precio(n):
    return "$" + f"{n:,}".replace(",", ".") + " COP"


def _tarjeta(p):
    e = html.escape
    img = (f'<img loading="lazy" src="/{e(p["imagenes"][0])}" alt="{e(p["nombre"])}" />'
           if p["imagenes"] else "")
    bp = '<span class="badge-bp">Bajo pedido</span>' if p["bajo_pedido"] else ""
    precio = (f'<span class="price">{_precio(p["precio"])}</span>' if p["precio"]
              else '<span class="price consult">Consultar precio</span>')
    return (f'<article class="card" data-code="{e(p["codigo"])}"><div class="card-img js-open">{img}{bp}</div>'
            f'<div class="card-body"><button type="button" class="card-name js-open">{e(p["nombre"])}</button>'
            f'{precio}<button class="btn btn-primary js-add">Agregar</button></div></article>')


def _ld_lista(cat, lista):
    items = []
    for i, p in enumerate(lista, 1):
        prod = {"@type": "Product", "name": p["nombre"], "sku": p["codigo"], "category": cat["nombre"]}
        if p["imagenes"]: prod["image"] = f'{SITIO}/{p["imagenes"][0].split("?")[0]}'
        if p["descripcion"]: prod["description"] = p["descripcion"]
        if p["precio"]:
            prod["offers"] = {"@type": "Offer", "price": p["precio"], "priceCurrency": "COP",
                              "availability": "https://schema.org/" + ("BackOrder" if p["bajo_pedido"] else "InStock"),
                              "url": f'{SITIO}/c/{cat["slug"]}/'}
        items.append({"@type": "ListItem", "position": i, "item": prod})
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": f'{cat["nombre"]} en {ZONA}',
          "numberOfItems": len(lista), "itemListElement": items}
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"


def generar(proj, productos, categorias):
    ruta_index = os.path.join(proj, "index.html")
    with open(ruta_index, encoding="utf-8", newline="") as f: base = f.read()
    nl = "\r\n" if "\r\n" in base else "\n"
    base = base.replace("\r\n", "\n")
    activos = [p for p in productos if p.get("activo", True)]
    usadas = [c for c in categorias if any(p["categoria"] == c["slug"] for p in activos)]

    # 1) enlaces del pie (en el home y en cada categoría)
    enlaces = ('<nav class="foot-cats" aria-label="Todas las categorías"><span class="foot-cats-title">Categorías</span>'
               + "".join(f'<a href="/c/{c["slug"]}/">{html.escape(c["nombre"])}</a>' for c in usadas) + "</nav>")
    base = _bloque(base, "CATS", enlaces)
    with open(ruta_index, "w", encoding="utf-8", newline="") as f: f.write(base.replace("\n", nl))

    # 2) una página por categoría
    raiz_c = os.path.join(proj, "c")
    for viejo in (os.listdir(raiz_c) if os.path.isdir(raiz_c) else []):   # categorías que ya no existen
        if viejo not in {c["slug"] for c in usadas}:
            vp = os.path.join(raiz_c, viejo, "index.html")
            if os.path.exists(vp): os.remove(vp)
            try: os.rmdir(os.path.join(raiz_c, viejo))
            except OSError: pass
    for c in usadas:
        lista = [p for p in activos if p["categoria"] == c["slug"]]
        nombre = html.escape(c["nombre"]); url = f'{SITIO}/c/{c["slug"]}/'
        titulo = f'{nombre} en {ZONA} | Picardías Sex Shop'
        desc = (f'{nombre} en {ZONA}: {len(lista)} productos con foto y precio. '
                f'Pide por WhatsApp y recibe con envío discreto en {ZONA} y todo Colombia.')
        head = (f'\n<title>{titulo}</title>\n<meta name="description" content="{desc}" />\n'
                f'<link rel="canonical" href="{url}" />\n<meta property="og:title" content="{titulo}" />\n'
                f'<meta property="og:url" content="{url}" />\n')
        hero = (f'\n<section class="hero hero-cat"><div class="hero-inner">'
                f'<a class="crumb" href="/">Picardías · Todo el catálogo</a>'
                f'<h1 class="hero-title">{nombre}</h1>'
                f'<p class="hero-sub">{len(lista)} productos con envío discreto en {ZONA} y todo Colombia. '
                f'Arma tu pedido y confírmalo por WhatsApp.</p></div></section>\n')
        s = _bloque(base, "HEAD", head)
        s = _bloque(s, "HERO", hero)
        s = _bloque(s, "GRID", "".join(_tarjeta(p) for p in lista))
        s = _bloque(s, "LD", _ld_lista(c, lista))
        s = s.replace("<body>", f'<body data-cat="{c["slug"]}">', 1)
        os.makedirs(os.path.join(raiz_c, c["slug"]), exist_ok=True)
        with open(os.path.join(raiz_c, c["slug"], "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(s)

    # 3) sitemap
    hoy = datetime.date.today().isoformat()
    urls = [f"{SITIO}/"] + [f'{SITIO}/c/{c["slug"]}/' for c in usadas]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"  <url><loc>{u}</loc><lastmod>{hoy}</lastmod></url>" for u in urls]
    xml += ["</urlset>", ""]
    with open(os.path.join(proj, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(xml))
    print(f"SEO: {len(usadas)} páginas de categoría + sitemap.xml ({len(urls)} URLs)")
