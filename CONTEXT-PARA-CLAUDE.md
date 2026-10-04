# Picardías — Contexto técnico para modificaciones (brief para Claude)

> Pásale este archivo a Claude (Desktop) antes de pedir cambios. Describe qué es el sitio,
> cómo está construido y cómo tocar cada cosa sin romper el flujo. Proyecto en
> `D:\Documentos\picardias-web`. Repo PÚBLICO `matatanstudent10/picardias`. En vivo: **https://picardias.win**.

## 1. Qué es
Catálogo de tienda (productos para adultos) **100% estático** que reemplazó un PDF de 75 MB.
Muestra ~518 productos en 23 categorías, con buscador, filtro por categoría, modal de producto,
**carrito que arma el pedido por WhatsApp** (no hay pagos en línea), verificación de edad 18+ y un
panel de administración oculto (Decap CMS). WhatsApp de la tienda: `573014011376`.

## 2. Stack y filosofía (NO cambiar sin motivo)
- **HTML + CSS + JavaScript vanilla.** Sin React, sin frameworks, sin bundler, sin `npm` en el front.
- **Sin backend.** Se sirve en **GitHub Pages**. Un sitio estático no recibe "subidas": los cambios de
  datos entran por git (Decap CMS) o editando los `.md` a mano.
- **Fuente de verdad de los datos:** los archivos `content/productos/*.md`. Un script los compila a
  `public/products.json`, que es lo único que lee el navegador.
- Reglas de oro: **no introducir dependencias ni build steps**; **no mover `products.json` ni las rutas
  `public/img/<codigo>/`**; mantener todo compatible con GitHub Pages (ojo con el gotcha de `_` abajo).

## 3. Árbol de archivos
```
index.html                 una sola página: age gate, topbar, hero, chips de categoría,
                           grid, modal de producto, carrito, botón flotante de WhatsApp
assets/
  styles.css               TODO el CSS. Tokens de marca en :root (paleta). Tema oscuro.
  app.js                   TODA la lógica. Vanilla, IIFE. Sin dependencias.
  brand/                   logo.png, logo_menu.png, hero.jpg, hero_movil.jpg, og.jpg, favicon.png, wa.png
public/
  products.json            catálogo COMPILADO (lo consume app.js). NO editar a mano.
  img/<codigo>/1.webp …    fotos por producto (WebP)
  img/_pool/               TODAS las fotos extraídas del PDF (para reasignar en el admin)
  img/uploads/             fotos que sube Decap
content/productos/*.md     1 archivo por producto (frontmatter). FUENTE DE VERDAD. Lo edita Decap.
admin/
  config.yml               Decap CMS: colección "productos", lista de categorías, backend github
  index.html               carga Decap CMS
scripts/
  compilar.py              md -> products.json  (lo corre el GitHub Action; sin librerías externas)
  extraer_catalogo.py      PDF -> md + imágenes (PyMuPDF/Pillow). Solo si cambia el PDF.
  extraer_lenceria.py      igual, para el PDF de lencería (otro formato)
  recategorizar.py         reasigna categoría por rango de códigos
.github/workflows/build.yml  Action: al cambiar content/productos/** recompila products.json y lo commitea
CNAME                      picardias.win
.nojekyll                  OBLIGATORIO (ver gotcha)
```

## 4. Flujo de datos (de punta a punta)
```
Editas en /admin (Decap)  ->  commit a content/productos/<codigo>.md
        ->  GitHub Action corre scripts/compilar.py
        ->  regenera public/products.json  y lo commitea
        ->  GitHub Pages publica  ->  app.js hace fetch de products.json  ->  render
```
Cambios de **código** (HTML/CSS/JS): editas el archivo, commit/push, Pages publica en ~1 min.

## 5. Modelo de datos
**Un producto en `content/productos/<codigo>.md`** (solo frontmatter YAML, sin cuerpo):
```yaml
---
codigo: "01"                     # ID único (string). Principales son numéricos; lencería tipo "conjunto-8668"
nombre: "Lubricante caliente sabor mango biche"
precio: 18400                    # entero en COP. 0/ausente => la web muestra "Consultar"
categoria: lubricantes-calientes # debe ser uno de los slugs de la lista (sección 8)
imagenes:
  - public/img/01/1.webp         # rutas relativas; la primera es la portada
descripcion: ""
activo: true                     # false => no aparece en la tienda
bajo_pedido: true                # opcional; muestra badge y aviso "no entrega al día siguiente" (lencería)
destacado: true                  # opcional (default false); el producto aparece en la portada
---
```
Las rutas de `imagenes` en los `.md` van **SIN query** (`?v=`); así las guarda Decap y así deben quedar.
**`public/products.json`** (lo genera compilar.py):
```json
{
  "categorias": [{ "slug": "lubricantes-calientes", "nombre": "Lubricantes Calientes" }, ...],
  "productos":  [{ "codigo":"01","nombre":"...","precio":18400,"categoria":"...",
                   "imagenes":["public/img/01/1.webp?v=3f2a9c1b"],"descripcion":"","activo":true,
                   "bajo_pedido":false,"destacado":false }, ...]
}
```
**Cache-busting:** compilar.py añade a cada imagen que existe en disco `?v=` + los 8 primeros caracteres
del md5 del archivo. Si cambias una foto conservando el nombre, cambia el `?v=` y los celulares la
vuelven a descargar. Rutas cuyo archivo no existe se dejan tal cual (sin `?v=`).

## 6. Cómo funciona cada archivo clave
- **index.html**: estructura estática. IDs importantes que usa el JS: `#ageGate/#ageYes`, `#search`,
  `#cats` (chips), `#grid`, `#modal` (+`#mImg #mCode #mName #mPrice #mBP #mDesc #mQty #mAdd`),
  `#cart #cartItems #cartTotal #checkout #cartCount #cartBtn`, `#overlay`, `#waFloat #waLink`.
  Carga fuentes Google (Cormorant Garamond + Inter) y `assets/styles.css`; al final `assets/app.js` con `defer`.
- **assets/app.js** (IIFE, vanilla). Config arriba: `WHATSAPP` y `MONEDA`. Funciones:
  `ageGate()` (recuerda en localStorage `pic_age_ok`), `cargar()` (fetch de products.json, filtra `activo!==false`),
  `renderCats()` (chips por categoría con conteo), `render()`/`visibles()` (filtro+búsqueda por nombre/código),
  `abrirModal()`, carrito en localStorage `pic_cart` (`addCart/setQty/pintarCart/openCart`),
  `checkout()` (arma el texto y abre `wa.me`). `esc()` escapa HTML. `show/hide` usan el atributo `hidden`.
- **assets/styles.css**: tema oscuro, mobile-first. **Paleta en `:root`** (sección 7). Componentes:
  `.btn/.btn-primary/.btn-wa`, `.age-gate`, `.topbar` (sticky), `.hero`, `.cats .chip`, `.grid .card`,
  `.modal`, `.cart`, `.wa-float`, `.footer`. Regla clave: `[hidden]{display:none!important}`.
- **scripts/compilar.py**: lee los `.md`, parsea el frontmatter (parser propio, sin PyYAML), ordena por
  número de código, arma `categorias` (solo las usadas, en orden fijo `CAT_ORDER`) y escribe products.json.
- **.github/workflows/build.yml**: se dispara al cambiar `content/productos/**` o `compilar.py`; corre
  compilar.py y commitea products.json si cambió. Python 3.12, sin dependencias.
- **admin/config.yml**: Decap. `backend: github` repo `matatanstudent10/picardias`, `base_url` = Worker OAuth.
  Colección `productos` (folder `content/productos`, slug = codigo). La **lista de categorías está aquí**
  (hay que mantenerla en espejo con `CAT_ORDER` de compilar.py).

## 7. Paleta y tipografía (tokens en `assets/styles.css :root`)
```css
--bg:#0e0709; --bg-2:#170d13; --bg-3:#20131c;     /* fondos oscuros */
--pink:#f0287a; --pink-2:#ff4d97; --gold:#e7b667; /* marca */
--text:#f6ebf1; --muted:#b9899f;                  /* texto */
--serif:"Cormorant Garamond"; --sans:"Inter";
--radius:16px; --maxw:1180px;
```
Para recolorear la marca, cambiar `--pink/--pink-2` (y `--gold`). Todo lo demás los referencia.

## 8. Slugs de categoría válidos (deben coincidir en los .md, en config.yml y en CAT_ORDER)
`lubricantes-calientes, electrizantes, frio-caliente, neutros-saborizados, multiorgasmo, anales, retardantes, estrechantes,
potenciadores, para-masajes, kits, feromonas, juegos, anillos-fundas, balas-huevos, arnes-sado, lenceria,
plug-anal, masturbadores, masajeadores, vibradores-con-pila, vibradores-clitoris, vibradores, vibradores-con-app,
succionadores, otros`

## 9. Despliegue
- **GitHub Pages**: Settings → Pages → Deploy from branch → `main` / `/ (root)`.
- **Dominio**: `picardias.win` en Cloudflare. CNAME `@` y `www` → `matatanstudent10.github.io`
  (empezar en **nube gris / DNS only**), archivo `CNAME` en el repo, Enforce HTTPS.
- **Admin (Decap)**: necesita un **broker OAuth gratis** (Cloudflare Worker, p. ej. `sveltia-cms-auth`)
  + una OAuth App de GitHub (Client ID/Secret). `base_url` en config.yml apunta al Worker. (Pendiente de montar.)

## 10. GOTCHAS críticos (no repetir estos errores)
- **`.nojekyll` es obligatorio.** GitHub Pages (Jekyll) ignora carpetas que empiezan con `_`
  (ej. `public/img/_pool/`). Sin `.nojekyll` esas imágenes dan 404.
- **`[hidden]{display:none!important}`** debe existir: el atributo `hidden` lo anula cualquier regla
  con `display:flex/grid`. Síntoma típico: un botón/modal que "no hace nada" al cerrarse.
- **products.json NO se edita a mano**: lo pisa el Action. Editar los `.md`.
- **Imágenes del PDF**: el emparejamiento foto↔producto salió por posición y puede estar mal; en
  `public/img/_pool/` están todas para reasignar. Filtrar imágenes por tamaño puede botar fotos válidas.
- **Categorías por rango de código** (recategorizar.py) es más fiable que "último encabezado visto".
- **Encoding del PDF**: traía acentos rotos (`corazón`→`coraz?n`); se arregló con reemplazos, no con el extractor.
- Repo **público** → nunca meter aquí datos privados (esto no pertenece a la bóveda de EYE).

## 11. Recetas de cambios comunes (para pedirle a Claude)
- **Cambiar el WhatsApp**: `assets/app.js`, constante `WHATSAPP` (formato internacional sin `+`).
- **Cambiar un precio/nombre/foto**: editar el `content/productos/<codigo>.md` (o por el admin). El Action recompila.
- **Ocultar un producto**: `activo: false` en su `.md`.
- **Destacar un producto en la portada**: `destacado: true` en su `.md` (o el interruptor "Destacado" en el admin).
- **Agregar un producto**: crear `content/productos/<codigo>.md` con el frontmatter de la sección 5 y subir su foto a `public/img/<codigo>/1.webp`.
- **Recolorear la marca**: variables `--pink/--pink-2/--gold` en `styles.css :root`.
- **Agregar/renombrar una categoría**: editarla en TRES sitios en espejo — `CAT_ORDER` en `scripts/compilar.py`,
  la lista `options` en `admin/config.yml`, y el campo `categoria` de los `.md` afectados.
- **Grupos de la barra de categorías**: constante `GRUPOS` arriba en `assets/app.js` (5 grupos → slugs). Una categoría nueva
  sin grupo cae sola en el último ("Juegos y más"); para ubicarla bien, agrégala al grupo que corresponda.
- **Íconos**: sprite SVG de Lucide (licencia ISC) al inicio de `index.html`; se usan con `<svg class="i"><use href="#i-nombre"/></svg>`.
  Para uno nuevo, copia el `<path>` desde lucide.dev a un `<symbol id="i-…">`. No usar emojis en la interfaz.
- Tras cualquier cambio de datos local, para ver el sitio: `python -m http.server 8099` y abrir `http://127.0.0.1:8099`.
  Si editaste `.md` en local, corre `python scripts/compilar.py` para regenerar products.json antes de mirar.

## 12. Reglas para quien modifique
1. Mantener **estático y sin dependencias** nuevas en el front.
2. No romper los **IDs** que usa `app.js` (sección 6) al tocar el HTML.
3. No mover `public/products.json` ni el esquema de `public/img/<codigo>/`.
4. Categorías siempre **en espejo** (compilar.py ↔ config.yml ↔ .md).
5. Probar en móvil (el diseño es mobile-first) y verificar que el age gate y el carrito sigan funcionando.
