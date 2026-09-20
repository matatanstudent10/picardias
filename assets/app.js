/* Picardías — catálogo estático. Sin dependencias. */
(() => {
  "use strict";

  // ====== CONFIGURA ESTO ======
  const WHATSAPP = "573014011376";           // línea de la tienda (formato internacional, sin +)
  const MONEDA = "$";                        // símbolo de precio
  // =============================

  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const fmt = (n) => MONEDA + (n || 0).toLocaleString("es-CO");
  const waUrl = (txt) => `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(txt)}`;

  let PRODUCTOS = [], CATS = [], filtro = "all", q = "";
  let cart = cargarCart();

  // ---------- Age gate ----------
  function ageGate() {
    const g = $("#ageGate");
    if (localStorage.getItem("pic_age_ok") === "1") { g.hidden = true; return; }
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
    renderCats(); render();
  }

  // ---------- Categorías ----------
  function renderCats() {
    const nav = $("#cats");
    const chips = [`<button class="chip active" data-cat="all">Todas</button>`];
    for (const c of CATS) {
      const n = PRODUCTOS.filter(p => p.categoria === c.slug).length;
      if (n) chips.push(`<button class="chip" data-cat="${c.slug}">${c.nombre}</button>`);
    }
    nav.innerHTML = chips.join("");
    $$(".chip", nav).forEach(ch => ch.addEventListener("click", () => {
      filtro = ch.dataset.cat;
      $$(".chip", nav).forEach(x => x.classList.remove("active"));
      ch.classList.add("active");
      render();
      document.getElementById("catalogo").scrollIntoView({ behavior: "smooth", block: "start" });
    }));
  }

  // ---------- Render grid ----------
  function visibles() {
    const term = q.trim().toLowerCase();
    return PRODUCTOS.filter(p => {
      if (filtro !== "all" && p.categoria !== filtro) return false;
      if (term && !(`${p.nombre} ${p.codigo}`.toLowerCase().includes(term))) return false;
      return true;
    });
  }
  function render() {
    const grid = $("#grid"), list = visibles();
    $("#empty").hidden = list.length > 0;
    $("#resultInfo").textContent = `${list.length} producto${list.length === 1 ? "" : "s"}`;
    grid.innerHTML = list.map(p => {
      const img = p.imagenes && p.imagenes[0]
        ? `<img loading="lazy" src="${p.imagenes[0]}" alt="${esc(p.nombre)}" />`
        : `<div class="card-noimg">P</div>`;
      return `<article class="card" data-code="${p.codigo}">
        <div class="card-img js-open">${img}</div>
        <div class="card-body">
          <span class="code">Cód. ${p.codigo}</span>
          <span class="card-name js-open">${esc(p.nombre)}</span>
          ${p.precio ? `<span class="price">${fmt(p.precio)}</span>` : `<span class="price" style="font-size:.9rem;color:var(--muted)">Consultar</span>`}
          <button class="btn btn-primary js-add">Agregar</button>
        </div></article>`;
    }).join("");
    $$(".card", grid).forEach(card => {
      const code = card.dataset.code;
      $$(".js-open", card).forEach(el => el.addEventListener("click", () => abrirModal(code)));
      $(".js-add", card).addEventListener("click", () => { addCart(code, 1); toast(); });
    });
  }

  // ---------- Modal ----------
  let modalCode = null, modalQty = 1;
  function abrirModal(code) {
    const p = PRODUCTOS.find(x => x.codigo === code); if (!p) return;
    modalCode = code; modalQty = 1;
    $("#mImg").src = (p.imagenes && p.imagenes[0]) || "assets/brand/logo.png";
    $("#mImg").alt = p.nombre;
    $("#mCode").textContent = "Cód. " + p.codigo;
    $("#mName").textContent = p.nombre;
    $("#mPrice").textContent = p.precio ? fmt(p.precio) : "Consultar";
    $("#mDesc").textContent = p.descripcion || "";
    $("#mQty").textContent = "1";
    show("#modal");
  }
  function bindModal() {
    $("#modalClose").addEventListener("click", () => hide("#modal"));
    $("#modal").addEventListener("click", e => { if (e.target.id === "modal") hide("#modal"); });
    $(".qminus").addEventListener("click", () => { modalQty = Math.max(1, modalQty - 1); $("#mQty").textContent = modalQty; });
    $(".qplus").addEventListener("click", () => { modalQty++; $("#mQty").textContent = modalQty; });
    $("#mAdd").addEventListener("click", () => { addCart(modalCode, modalQty); hide("#modal"); openCart(); });
  }

  // ---------- Carrito ----------
  function cargarCart() { try { return JSON.parse(localStorage.getItem("pic_cart") || "{}"); } catch (e) { return {}; } }
  function guardarCart() { try { localStorage.setItem("pic_cart", JSON.stringify(cart)); } catch (e) {} }
  function addCart(code, qty) { cart[code] = (cart[code] || 0) + qty; guardarCart(); pintarCart(); }
  function setQty(code, qty) { if (qty <= 0) delete cart[code]; else cart[code] = qty; guardarCart(); pintarCart(); }
  function totalItems() { return Object.values(cart).reduce((a, b) => a + b, 0); }
  function totalPrecio() {
    return Object.entries(cart).reduce((s, [c, q]) => {
      const p = PRODUCTOS.find(x => x.codigo === c); return s + (p && p.precio ? p.precio * q : 0);
    }, 0);
  }
  function pintarCart() {
    $("#cartCount").textContent = totalItems();
    const box = $("#cartItems"), codes = Object.keys(cart);
    if (!codes.length) { box.innerHTML = `<p class="cart-empty">Tu pedido está vacío.</p>`; }
    else {
      box.innerHTML = codes.map(c => {
        const p = PRODUCTOS.find(x => x.codigo === c); if (!p) return "";
        const img = p.imagenes && p.imagenes[0] ? `<img src="${p.imagenes[0]}" alt="">` : `<img alt="">`;
        return `<div class="ci" data-code="${c}">${img}
          <div class="ci-info"><span class="code">Cód. ${c}</span>${esc(p.nombre)}
            <div class="ci-qty"><button class="cm">−</button><span>${cart[c]}</span><button class="cp">+</button>
            <span class="ci-price">${p.precio ? fmt(p.precio * cart[c]) : "Consultar"}</span></div>
          </div><button class="ci-rm" title="Quitar">🗑</button></div>`;
      }).join("");
      $$(".ci", box).forEach(row => {
        const c = row.dataset.code;
        $(".cm", row).addEventListener("click", () => setQty(c, cart[c] - 1));
        $(".cp", row).addEventListener("click", () => setQty(c, cart[c] + 1));
        $(".ci-rm", row).addEventListener("click", () => setQty(c, 0));
      });
    }
    $("#cartTotal").textContent = fmt(totalPrecio());
  }
  function openCart() { show("#cart"); $("#overlay").hidden = false; }
  function closeCart() { hide("#cart"); $("#overlay").hidden = true; }

  function checkout() {
    const codes = Object.keys(cart);
    if (!codes.length) { alert("Tu pedido está vacío."); return; }
    let msg = "¡Hola Picardías! Quiero pedir:\n\n";
    codes.forEach(c => {
      const p = PRODUCTOS.find(x => x.codigo === c); if (!p) return;
      msg += `• ${cart[c]} x [${c}] ${p.nombre}${p.precio ? " — " + fmt(p.precio * cart[c]) : ""}\n`;
    });
    msg += `\nTotal: ${fmt(totalPrecio())}`;
    window.open(waUrl(msg), "_blank");
  }

  // ---------- utils ----------
  function esc(s) { return (s || "").replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m])); }
  function show(sel) { $(sel).hidden = false; document.body.classList.add("locked"); }
  function hide(sel) { $(sel).hidden = true; if (!isOpen("#modal") && !isOpen("#cart")) document.body.classList.remove("locked"); }
  function isOpen(sel) { return !$(sel).hidden; }
  let toastT; function toast() {
    let t = $("#toast"); if (!t) { t = document.createElement("div"); t.id = "toast";
      t.style.cssText = "position:fixed;bottom:84px;left:50%;transform:translateX(-50%);background:var(--pink);color:#fff;padding:.6rem 1.2rem;border-radius:999px;z-index:70;font-size:.9rem;box-shadow:var(--shadow)";
      document.body.appendChild(t); }
    t.textContent = "Agregado al pedido ✓"; t.style.opacity = "1";
    clearTimeout(toastT); toastT = setTimeout(() => t.style.opacity = "0", 1400);
  }

  // ---------- init ----------
  document.addEventListener("DOMContentLoaded", () => {
    ageGate(); bindModal(); pintarCart();
    $("#search").addEventListener("input", e => { q = e.target.value; render(); });
    $("#cartBtn").addEventListener("click", openCart);
    $("#cartClose").addEventListener("click", closeCart);
    $("#overlay").addEventListener("click", closeCart);
    $("#checkout").addEventListener("click", checkout);
    const wa = waUrl("¡Hola Picardías! Tengo una consulta 😊");
    $("#waFloat").href = wa; $("#waLink").href = wa;
    cargar();
  });
})();
