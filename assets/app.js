/* Picardías — catálogo estático. Sin dependencias. */
(() => {
  "use strict";

  // ====== CONFIGURA ESTO ======
  const WHATSAPP = "573014011376";           // línea de la tienda (formato internacional, sin +)
  const MONEDA = "$";                        // símbolo de precio
  // Grupos de la barra de categorías (slugs de compilar.py). Un slug sin grupo cae en el último.
  const GRUPOS = [
    { id: "lubricantes", nombre: "Lubricantes", icon: "droplet",
      cats: ["lubricantes-calientes", "electrizantes", "frio-caliente", "neutros-saborizados", "multiorgasmo", "anales"] },
    { id: "bienestar", nombre: "Bienestar", icon: "sparkles",
      cats: ["retardantes", "estrechantes", "potenciadores", "feromonas", "para-masajes"] },
    { id: "juguetes", nombre: "Juguetes", icon: "heart",
      cats: ["vibradores", "vibradores-clitoris", "vibradores-con-pila", "vibradores-con-app", "succionadores",
             "balas-huevos", "masajeadores", "masturbadores", "plug-anal", "anillos-fundas"] },
    { id: "lenceria", nombre: "Lencería", icon: "gem", cats: ["lenceria", "arnes-sado"] },
    { id: "juegos", nombre: "Juegos y más", icon: "dices", cats: ["juegos", "kits", "otros"] },
  ];
  // =============================

  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const fmt = (n) => MONEDA + (n || 0).toLocaleString("es-CO") + " COP";
  const waUrl = (txt) => `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(txt)}`;
  const ic = (name) => `<svg class="i" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  let PRODUCTOS = [], CATS = [], CAT_NOMBRE = {}, GRUPO_DE = {};
  let grupo = "all", cat = "all", q = "", entrega = "todos", orden = "rel";
  let cart = cargarCart();

  // ---------- Age gate ----------
  function ageGate() {
    const g = $("#ageGate");
    let ok = false;
    try { ok = localStorage.getItem("pic_age_ok") === "1"; } catch (e) {}
    if (ok) { g.hidden = true; return; }
    g.hidden = false; document.body.classList.add("locked");
    $("#ageYes").addEventListener("click", () => {
      try { localStorage.setItem("pic_age_ok", "1"); } catch (e) {}
      g.hidden = true; document.body.classList.remove("locked");
    });
  }

  // ---------- Carga de datos ----------
  async function cargar() {
    try {
      const r = await fetch("public/products.json", { cache: "no-store" });
      const d = await r.json();
      PRODUCTOS = (d.productos || []).filter(p => p.activo !== false);
      CATS = d.categorias || [];
    } catch (e) {
      $("#grid").innerHTML = "<p class='empty'>No se pudo cargar el catálogo.</p>";
      return;
    }
    CATS.forEach(c => { CAT_NOMBRE[c.slug] = c.nombre; });
    const ultimo = GRUPOS[GRUPOS.length - 1];
    GRUPOS.forEach(g => g.cats.forEach(s => { GRUPO_DE[s] = g.id; }));
    CATS.forEach(c => { if (!GRUPO_DE[c.slug]) { GRUPO_DE[c.slug] = ultimo.id; ultimo.cats.push(c.slug); } });
    PRODUCTOS.forEach(p => { p._q = norm(`${p.nombre} ${p.codigo} ${CAT_NOMBRE[p.categoria] || ""}`); });
    // el carrito guardado puede traer productos que ya no existen o se ocultaron
    Object.keys(cart).forEach(c => { if (!porCodigo(c)) delete cart[c]; });
    guardarCart(); pintarCart();
    renderGrupos(); renderFeatured(); render();
  }
  const porCodigo = (c) => PRODUCTOS.find(p => p.codigo === c);

  // ---------- Categorías: grupos + subcategorías ----------
  const contar = (slugs) => PRODUCTOS.filter(p => slugs.includes(p.categoria)).length;
  function renderGrupos() {
    const btns = [`<button class="grp${grupo === "all" ? " active" : ""}" data-grp="all" aria-pressed="${grupo === "all"}">${ic("grid")}<span>Todo</span><small>${PRODUCTOS.length}</small></button>`];
    for (const g of GRUPOS) {
      const n = contar(g.cats);
      if (n) btns.push(`<button class="grp${grupo === g.id ? " active" : ""}" data-grp="${g.id}" aria-pressed="${grupo === g.id}">${ic(g.icon)}<span>${g.nombre}</span><small>${n}</small></button>`);
    }
    $("#groups").innerHTML = btns.join("");
    renderSubcats();
  }
  function renderSubcats() {
    const box = $("#subcats"), g = GRUPOS.find(x => x.id === grupo);
    const subs = g ? CATS.filter(c => g.cats.includes(c.slug) && contar([c.slug])) : [];
    if (subs.length < 2) { box.hidden = true; box.innerHTML = ""; fijarAlto(); return; }
    box.hidden = false;
    box.innerHTML = [`<button class="chip${cat === "all" ? " active" : ""}" data-cat="all" aria-pressed="${cat === "all"}">Todo ${esc(g.nombre.toLowerCase())}</button>`]
      .concat(subs.map(c => `<button class="chip${cat === c.slug ? " active" : ""}" data-cat="${esc(c.slug)}" aria-pressed="${cat === c.slug}">${esc(c.nombre)}<small>${contar([c.slug])}</small></button>`))
      .join("");
    fijarAlto();
  }
  // alturas reales de las barras fijas (para el sticky y los anclajes #catalogo)
  function fijarAlto() {
    document.documentElement.style.setProperty("--topbar-h", $(".topbar").offsetHeight + "px");
    document.documentElement.style.setProperty("--cats-h", $("#cats").offsetHeight + "px");
  }
  // la barra de categorías es sticky: lleva al inicio de los resultados, justo debajo de ella
  function irAlCatalogo() {
    const top = $("#catalogo").offsetTop - $(".topbar").offsetHeight - $("#cats").offsetHeight;
    window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }

  // ---------- Listado ----------
  function visibles() {
    const terms = norm(q).split(/\s+/).filter(Boolean);
    const g = GRUPOS.find(x => x.id === grupo);
    const list = PRODUCTOS.filter(p => {
      if (g && !g.cats.includes(p.categoria)) return false;
      if (cat !== "all" && p.categoria !== cat) return false;
      if (entrega === "inmediata" && p.bajo_pedido) return false;
      if (entrega === "pedido" && !p.bajo_pedido) return false;
      return terms.every(t => p._q.includes(t));
    });
    if (orden !== "rel") {
      const s = orden === "asc" ? 1 : -1;   // "Consultar" (sin precio) siempre al final
      list.sort((a, b) => (!a.precio) - (!b.precio) || s * (a.precio - b.precio));
    }
    return list;
  }
  function tarjeta(p) {
    const img = p.imagenes && p.imagenes[0]
      ? `<img loading="lazy" src="${esc(p.imagenes[0])}" alt="${esc(p.nombre)}" onerror="this.onerror=null;this.src='assets/brand/logo.png'" />`
      : `<div class="card-noimg">${ic("package")}</div>`;
    const bp = p.bajo_pedido ? `<span class="badge-bp">${ic("clock")}Bajo pedido</span>` : "";
    const precio = p.precio ? `<span class="price">${fmt(p.precio)}</span>` : `<span class="price consult">Consultar precio</span>`;
    return `<article class="card" data-code="${esc(p.codigo)}">
      <div class="card-img js-open">${img}${bp}</div>
      <div class="card-body">
        <button type="button" class="card-name js-open">${esc(p.nombre)}</button>
        ${precio}
        <button class="btn btn-primary js-add">Agregar</button>
      </div></article>`;
  }
  function render() {
    const grid = $("#grid"), list = visibles();
    $("#empty").hidden = list.length > 0;
    const donde = cat !== "all" ? CAT_NOMBRE[cat] : (GRUPOS.find(x => x.id === grupo) || {}).nombre;
    $("#resultInfo").textContent = `${list.length} producto${list.length === 1 ? "" : "s"}${donde ? " en " + donde : ""}`;
    const notice = $("#notice"), hayBP = list.some(p => p.bajo_pedido);
    notice.hidden = !hayBP || entrega === "pedido";
    if (hayBP) notice.innerHTML = `${ic("clock")}<span><strong>Bajo pedido:</strong> los artículos marcados no son de entrega al día siguiente. Se encargan y se coordina la entrega por WhatsApp.</span>`;
    grid.innerHTML = list.map(tarjeta).join("");
    $("#featured").hidden = !(grupo === "all" && !q.trim() && entrega === "todos" && $("#featRow").children.length);
  }
  function renderFeatured() {
    const dest = PRODUCTOS.filter(p => p.destacado);
    $("#featRow").innerHTML = dest.map(tarjeta).join("");
  }
  // un solo listener por contenedor (sirve para grilla y destacados)
  function bindTarjetas(cont) {
    cont.addEventListener("click", e => {
      const card = e.target.closest(".card"); if (!card) return;
      const code = card.dataset.code;
      if (e.target.closest(".js-add")) { addCart(code, 1); toast(); }
      else if (e.target.closest(".js-open")) abrirModal(code);
    });
  }

  // ---------- Modal + galería ----------
  let modalCode = null, modalQty = 1, gal = [], galIdx = 0, lastFocus = null;
  function abrirModal(code) {
    const p = porCodigo(code); if (!p) return;
    modalCode = code; modalQty = 1; lastFocus = document.activeElement;
    gal = (p.imagenes || []).filter(Boolean);
    if (!gal.length) gal = ["assets/brand/logo.png"];
    $("#mImg").alt = p.nombre;
    $("#mThumbs").innerHTML = gal.length > 1
      ? gal.map((src, i) => `<button class="thumb" data-i="${i}" aria-label="Foto ${i + 1}"><img src="${esc(src)}" alt="" loading="lazy" onerror="this.onerror=null;this.src='assets/brand/logo.png'" /></button>`).join("") : "";
    $("#mThumbs").hidden = gal.length < 2;
    $("#mPrev").hidden = $("#mNext").hidden = gal.length < 2;
    verFoto(0);
    $("#mCode").textContent = "Ref. " + p.codigo;
    $("#mName").textContent = p.nombre;
    $("#mPrice").textContent = p.precio ? fmt(p.precio) : "Precio por consultar";
    $("#mPrice").classList.toggle("consult", !p.precio);
    $("#mBP").hidden = !p.bajo_pedido;
    $("#mDesc").textContent = p.descripcion || "";
    $("#mQty").textContent = "1";
    $("#mAsk").href = waUrl(`Hola Picardías, quiero preguntar por este producto: [${p.codigo}] ${p.nombre}`);
    show("#modal");
    $("#modalClose").focus({ preventScroll: true });
  }
  function verFoto(i) {
    galIdx = (i + gal.length) % gal.length;
    $("#mImg").src = gal[galIdx];
    $$(".thumb", $("#mThumbs")).forEach((t, k) => t.classList.toggle("active", k === galIdx));
  }
  function bindModal() {
    $("#modalClose").addEventListener("click", () => hide("#modal"));
    $("#modal").addEventListener("click", e => { if (e.target.id === "modal") hide("#modal"); });
    $("#mPrev").addEventListener("click", () => verFoto(galIdx - 1));
    $("#mNext").addEventListener("click", () => verFoto(galIdx + 1));
    $("#mThumbs").addEventListener("click", e => { const t = e.target.closest(".thumb"); if (t) verFoto(+t.dataset.i); });
    let x0 = null;   // deslizar con el dedo
    $(".modal-img").addEventListener("touchstart", e => { x0 = e.touches[0].clientX; }, { passive: true });
    $(".modal-img").addEventListener("touchend", e => {
      if (x0 === null || gal.length < 2) return;
      const dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) verFoto(galIdx + (dx < 0 ? 1 : -1));
    });
    $(".qminus").addEventListener("click", () => { modalQty = Math.max(1, modalQty - 1); $("#mQty").textContent = modalQty; });
    $(".qplus").addEventListener("click", () => { modalQty++; $("#mQty").textContent = modalQty; });
    $("#mAdd").addEventListener("click", () => { addCart(modalCode, modalQty); hide("#modal"); openCart(); });
  }

  // ---------- Carrito ----------
  function cargarCart() {
    try { const o = JSON.parse(localStorage.getItem("pic_cart") || "{}"); return o && typeof o === "object" && !Array.isArray(o) ? o : {}; }
    catch (e) { return {}; }
  }
  function guardarCart() { try { localStorage.setItem("pic_cart", JSON.stringify(cart)); } catch (e) {} }
  function addCart(code, qty) { cart[code] = (cart[code] || 0) + qty; guardarCart(); pintarCart(); }
  function setQty(code, qty) { if (qty <= 0) delete cart[code]; else cart[code] = qty; guardarCart(); pintarCart(); }
  function totalItems() { return Object.values(cart).reduce((a, b) => a + b, 0); }
  function totalPrecio() {
    return Object.entries(cart).reduce((s, [c, n]) => { const p = porCodigo(c); return s + (p && p.precio ? p.precio * n : 0); }, 0);
  }
  function pintarCart() {
    const box = $("#cartItems"), codes = Object.keys(cart).filter(porCodigo);
    // antes de cargar el catálogo se muestra lo guardado; luego, solo lo que existe
    const n = PRODUCTOS.length ? codes.reduce((a, c) => a + cart[c], 0) : totalItems();
    $("#cartCount").textContent = n;
    $("#cartBtn").setAttribute("aria-label", `Ver pedido (${n} artículo${n === 1 ? "" : "s"})`);
    if (!codes.length) {
      box.innerHTML = `<div class="cart-empty">${ic("bag")}<p>Tu pedido está vacío.</p></div>`;
    } else {
      box.innerHTML = codes.map(c => {
        const p = porCodigo(c);
        const img = p.imagenes && p.imagenes[0] ? `<img src="${esc(p.imagenes[0])}" alt="" onerror="this.onerror=null;this.src='assets/brand/logo.png'">` : `<span class="ci-noimg">${ic("package")}</span>`;
        return `<div class="ci" data-code="${esc(c)}">${img}
          <div class="ci-info"><span class="ci-name">${esc(p.nombre)}</span>
            <div class="ci-qty"><button class="cm" aria-label="Menos">${ic("minus")}</button><span>${cart[c]}</span><button class="cp" aria-label="Más">${ic("plus")}</button>
            <span class="ci-price">${p.precio ? fmt(p.precio * cart[c]) : "Por consultar"}</span></div>
          </div><button class="ci-rm" aria-label="Quitar">${ic("trash")}</button></div>`;
      }).join("");
    }
    $("#cartTotal").textContent = fmt(totalPrecio());
    $("#cartConsult").hidden = !codes.some(c => !porCodigo(c).precio);
  }
  function bindCart() {
    $("#cartItems").addEventListener("click", e => {
      const row = e.target.closest(".ci"); if (!row) return;
      const c = row.dataset.code;
      if (e.target.closest(".cm")) setQty(c, cart[c] - 1);
      else if (e.target.closest(".cp")) setQty(c, cart[c] + 1);
      else if (e.target.closest(".ci-rm")) setQty(c, 0);
    });
  }
  function openCart() { show("#cart"); $("#overlay").hidden = false; }
  function closeCart() { hide("#cart"); $("#overlay").hidden = true; }

  function checkout() {
    const codes = Object.keys(cart).filter(porCodigo);
    if (!codes.length) { alert("Tu pedido está vacío."); return; }
    let msg = "Hola Picardías, quiero hacer este pedido:\n\n";
    let hayBP = false, hayConsulta = false;
    codes.forEach(c => {
      const p = porCodigo(c);
      if (p.bajo_pedido) hayBP = true;
      if (!p.precio) hayConsulta = true;
      msg += `- ${cart[c]} x [${c}] ${p.nombre}${p.bajo_pedido ? " (bajo pedido)" : ""}${p.precio ? " — " + fmt(p.precio * cart[c]) : " — precio por consultar"}\n`;
    });
    msg += `\nTotal: ${fmt(totalPrecio())}`;
    if (hayConsulta) msg += " (sin incluir los productos por consultar)";
    if (hayBP) msg += `\n\nNota: incluye artículos BAJO PEDIDO (no entrega al día siguiente).`;
    window.open(waUrl(msg), "_blank");
  }

  // ---------- utils ----------
  function esc(s) { return String(s || "").replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m])); }
  function show(sel) { $(sel).hidden = false; document.body.classList.add("locked"); }
  function hide(sel) {
    $(sel).hidden = true;
    if (!isOpen("#modal") && !isOpen("#cart")) document.body.classList.remove("locked");
    if (sel === "#modal" && lastFocus && document.contains(lastFocus)) lastFocus.focus({ preventScroll: true });
  }
  function isOpen(sel) { return !$(sel).hidden; }
  let toastT;
  function toast() {
    const t = $("#toast"), sp = $("span", t); sp.textContent = ""; setTimeout(() => { sp.textContent = "Agregado al pedido"; }, 30);
    t.classList.add("show");
    clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 1500);
  }

  // ---------- init ----------
  document.addEventListener("DOMContentLoaded", () => {
    ageGate(); bindModal(); bindCart(); pintarCart();
    fijarAlto(); window.addEventListener("resize", fijarAlto);
    bindTarjetas($("#grid")); bindTarjetas($("#featRow"));
    $("#search").addEventListener("input", e => { q = e.target.value; render(); });
    $("#groups").addEventListener("click", e => {
      const b = e.target.closest(".grp"); if (!b) return;
      grupo = b.dataset.grp; cat = "all";
      $$(".grp").forEach(x => { x.classList.toggle("active", x === b); x.setAttribute("aria-pressed", x === b); });
      const row = $("#groups"); row.scrollTo({ left: b.offsetLeft - (row.clientWidth - b.offsetWidth) / 2, behavior: "smooth" });
      renderSubcats(); render(); irAlCatalogo();
    });
    $("#subcats").addEventListener("click", e => {
      const b = e.target.closest(".chip"); if (!b) return;
      cat = b.dataset.cat;
      $$(".chip", $("#subcats")).forEach(x => { x.classList.toggle("active", x === b); x.setAttribute("aria-pressed", x === b); });
      render(); irAlCatalogo();
    });
    $$(".seg-btn").forEach(b => b.addEventListener("click", () => {
      entrega = b.dataset.ent;
      $$(".seg-btn").forEach(x => { x.classList.toggle("active", x === b); x.setAttribute("aria-pressed", x === b); });
      render();
    }));
    $("#sort").addEventListener("change", e => { orden = e.target.value; render(); });
    $("#cartBtn").addEventListener("click", openCart);
    $("#cartClose").addEventListener("click", closeCart);
    $("#overlay").addEventListener("click", closeCart);
    $("#checkout").addEventListener("click", checkout);
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") { if (isOpen("#modal")) hide("#modal"); else if (isOpen("#cart")) closeCart(); }
      if (e.key === "Tab" && isOpen("#modal")) {   // mantener el foco dentro del modal
        const f = $$("button:not([hidden]), a[href]", $(".modal-card")).filter(x => x.offsetParent);
        if (f.length && e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (f.length && !e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
      }
      if (isOpen("#modal") && gal.length > 1 && (e.key === "ArrowLeft" || e.key === "ArrowRight")) verFoto(galIdx + (e.key === "ArrowRight" ? 1 : -1));
    });
    const wa = waUrl("Hola Picardías, tengo una consulta.");
    $("#waFloat").href = wa; $("#waLink").href = wa;
    cargar();
  });
})();
