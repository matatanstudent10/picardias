# Picardías — Catálogo web

Catálogo estático, rápido y para móvil que **reemplaza el PDF de 75 MB**. Categorías,
buscador, carrito que arma el pedido por **WhatsApp**, verificación de edad (18+) y un
**panel de administración oculto** (Decap CMS) para editar precios y subir productos.

## Estructura
```
index.html            catálogo (age gate, grid, buscador, carrito)
assets/               css, js y marca (logos, hero, favicon)
public/products.json  catálogo compilado que consume la web
public/img/<código>/  fotos de producto (WebP)
public/img/_pool/      TODAS las fotos extraídas del PDF (para repicar en el admin)
content/productos/*.md un archivo por producto (lo edita Decap)
admin/                 Decap CMS (config.yml + index.html)
scripts/               extraer_catalogo.py (PDF→datos) y compilar.py (md→json)
.github/workflows/     recompila products.json en cada cambio
```

## 1. Configurar el WhatsApp
En `assets/app.js`, arriba, pon el número de la tienda (formato internacional, sin `+`):
```js
const WHATSAPP = "573001234567";
```

## 2. Ver el sitio localmente
```
python3 -m http.server 8099
```
Abre http://127.0.0.1:8099

## 3. Revisar el borrador (IMPORTANTE)
Los datos salieron del PDF automáticamente:
- **Nombres y precios:** ~98% correctos.
- **Categorías:** buen borrador; las secciones finales (lencería, plug, vibradores,
  succionadores, masajeadores) pueden estar mal ubicadas → **revisar en el admin**.
- **Fotos:** emparejadas por posición → **algunas no coinciden**. En `public/img/_pool/`
  están TODAS las fotos del PDF por si hay que reasignar una.

Puedes corregir todo desde el panel (paso 6) sin tocar código.

## 4. Regenerar desde el PDF (opcional)
Si cambia el PDF:
```
pip install pymupdf pillow
python3 scripts/extraer_catalogo.py "ruta/al/catálogo completo.pdf"
```

## 5. Subir a GitHub Pages
1. Crea un repositorio en GitHub y sube esta carpeta (`git init`, `add`, `commit`, `push`).
2. En el repo: **Settings → Pages → Build and deployment → Source: Deploy from a branch**,
   rama `main`, carpeta `/ (root)`. Guarda.
3. En 1-2 min el sitio queda en `https://USUARIO.github.io/REPO/`.
   > Para que las rutas funcionen mejor, usa un **dominio propio** (paso 7).

## 6. Panel de administración (Decap CMS)
Editas precios/fotos/productos desde `/admin` con login de GitHub. Como GitHub Pages no
tiene servidor, se necesita un **broker OAuth** (gratis, una sola vez):

**a) App OAuth en GitHub:** Settings → Developer settings → OAuth Apps → New:
   - Homepage: la URL de tu sitio.
   - Authorization callback URL: `https://TU-WORKER.workers.dev/callback`
   - Guarda el **Client ID** y **Client Secret**.

**b) Broker en Cloudflare Workers (gratis):** despliega un OAuth broker para Decap
   (por ejemplo el proyecto `sveltia-cms-auth` o `netlify-cms-oauth-provider` en un Worker),
   configúralo con el Client ID/Secret y anota su URL `https://TU-WORKER.workers.dev`.

**c) Edita `admin/config.yml`:** pon tu `repo: USUARIO/REPO` y
   `base_url: https://TU-WORKER.workers.dev`. Sube el cambio.

Entra a `https://tu-dominio/admin/`, inicia sesión con GitHub y listo.

### Flujo diario
Editas en `/admin` → se guarda un commit en el repo → el **GitHub Action** recompila
`public/products.json` → el sitio se actualiza solo en ~1 min.

## 7. Dominio propio (barato)
1. Compra el dominio (Namecheap, Porkbun, GoDaddy…).
2. En el DNS del dominio:
   - `CNAME`  `www`  →  `USUARIO.github.io`
   - (raíz) registros `A` a las IPs de GitHub Pages, o `ALIAS/ANAME` a `USUARIO.github.io`.
3. En GitHub → Settings → Pages → **Custom domain**: escribe tu dominio (crea el archivo `CNAME`).
4. Marca **Enforce HTTPS**.

## Notas
- Solo para mayores de 18 años (retail de productos para adultos). Presentación sobria + age gate.
- Sin pagos en línea: el pedido se cierra por WhatsApp.
- `noindex` está activo mientras montas; quítalo de `index.html` cuando quieras aparecer en Google.
