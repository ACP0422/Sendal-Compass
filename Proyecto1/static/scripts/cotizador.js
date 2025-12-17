const money = (n) => {
    if (n === null || n === undefined || n === "") return "—";
    const v = Number(n);
    if (Number.isNaN(v)) return "—";
    return v.toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  };
  
  const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = (val ?? "—");
  };
  
  function normalizeLotId(raw) {
    if (!raw) return null;
    const s = String(raw).trim().toUpperCase();
  
    const m = s.match(/^MZ(\d{2})-L0*(\d{1,3})$/i);
    if (m) return `MZ${m[1]}-L${String(Number(m[2])).padStart(2, "0")}`;
  
    if (/^MZ\d{2}-L\d{2}$/i.test(s)) return s;
  
    return null;
  }
  
  let panZoomInstance = null;
  
  function getSvgEl() {
    return document.querySelector("#mapWrap svg") || document.querySelector("svg");
  }
  
  function ensureViewBox(svg) {
    if (!svg) return;
    if (svg.getAttribute("viewBox")) return;
  
    const w = svg.getAttribute("width");
    const h = svg.getAttribute("height");
    if (w && h) svg.setAttribute("viewBox", `0 0 ${parseFloat(w)} ${parseFloat(h)}`);
  }
  
  function initPanZoom() {
    const svg = getSvgEl();
    if (!svg || typeof window.svgPanZoom !== "function") return;
  
    ensureViewBox(svg);
  
    if (panZoomInstance) {
      try { panZoomInstance.destroy(); } catch (e) {}
      panZoomInstance = null;
    }
  
    panZoomInstance = window.svgPanZoom(svg, {
      zoomEnabled: true,
      controlIconsEnabled: true,
      fit: true,
      center: true,
      minZoom: 0.5,
      maxZoom: 30,
      zoomScaleSensitivity: 0.25,
      dblClickZoomEnabled: false
    });
  
    refitMap();
    window.addEventListener("resize", refitMap);
  }
  
  function refitMap() {
    if (!panZoomInstance) return;
    panZoomInstance.resize();
    panZoomInstance.fit();
    panZoomInstance.center();
  }
  
  
  function closePanel() {
    const root = document.getElementById("cotizador");
    root?.classList.add("is-panel-closed");
    requestAnimationFrame(refitMap); // SOLO aquí para centrar cuando está cerrado
  }
  
  function openPanel() {
    const root = document.getElementById("cotizador");
    root?.classList.remove("is-panel-closed");
    // NO refit aquí para no romper zoom del usuario
  }
  


  function selectLotElement(el) {
    // quitar selección previa
    document.querySelectorAll(".lot-selected").forEach((n) => {
      n.classList.remove("lot-selected");
    });
  
    // marcar el actual
    el.classList.add("lot-selected");
  }
  
  
  async function loadLot(rawLotId) {
    const lotId = normalizeLotId(rawLotId);
    if (!lotId) return;
  
    const res = await fetch(`/api/lote/${encodeURIComponent(lotId)}/`);
  
    let data = null;
    try { data = await res.json(); } catch (e) {}
  
    if (!res.ok) return;
  
    const r = data.result;
  
    setText("panelTitle", `${r.id_lote} — ${String(r.estado_lote || "").toUpperCase()}`);
    setText("kvCodigo", r.id_lote);

    setText("kvPrecio", money(r.precio_total));
  
    setText("kvProyecto", r.proyecto);
    setText("kvManzana", r.manzana);
  
    setText("kvArea", r.superficie_m2);
    setText("kvPm2", money(r.precio_m2));
  
    setText("kvMedidas", r.medidas_lotes);
  
    setText("kvApartado", money(r.cantidad_de_apartado));
    setText("kvDias", r.dias_limite_apartado);
  
    setText("finEnganche", money(r.cantidad_enganche));
    setText("finFin", money(r.cantidad_financiamiento));
    setText("finMens", money(r.pago_mensualidad));
    setText("finLiq", money(r.cantidad_liquidacion));
  
    const img = document.getElementById("lotImg");
    if (img) img.src = r.url_imagen_lote || "";
  
    const hidden = document.getElementById("quoteLotCode");
    if (hidden) hidden.value = r.id_lote || "";
    console.log("hidden id_lote =", hidden?.value);




    openPanel();


  }
  
  function clearLotSelection() {
    document.querySelectorAll("#mapWrap svg .lot-selected").forEach((n) => {
      n.classList.remove("lot-selected");
    });
  }
  
  function selectLotElement(el) {
    clearLotSelection();
    el.classList.add("lot-selected");
  }
  
  function bindSvgLots() {
    const svg = getSvgEl();
    if (!svg) return;
  
    // SOLO shapes (no textos ni números)
    const nodes = svg.querySelectorAll(
      "path[id], polygon[id], rect[id], g[id][data-lot], path[data-lot], polygon[data-lot], rect[data-lot]"
    );
  
    nodes.forEach((el) => {
      const raw = el.getAttribute("data-lot") || el.id;
      const lotId = normalizeLotId(raw);
      if (!lotId) return;
  
      // SOLO etapa 4
      if (!lotId.startsWith("MZ04-")) return;
  
      // marcar como interactivo (hover)
      el.classList.add("lot-hover");
      el.style.cursor = "pointer";
  
      el.addEventListener("click", (e) => {
        e.stopPropagation();      // no rompe pan-zoom
        selectLotElement(el);     // borde verde
        loadLot(lotId);           // carga info
      });
    });
  }
  

  function showToast(msg, ok = false) {
    const box = document.getElementById("quoteToast");
    const text = document.getElementById("quoteToastMsg");
    if (!box || !text) return;
  
    box.classList.toggle("ok", ok);
    text.textContent = msg;
    box.hidden = false;
  
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => (box.hidden = true), 3500);
  }
  
  function clearFieldErrors(form) {
    form.querySelectorAll(".field-error").forEach((el) => {
      el.textContent = "";
      el.classList.remove("show");
    });
    form.querySelectorAll("input").forEach((inp) => inp.classList.remove("is-invalid"));
  }
  
  function applyFieldErrors(form, errors) {
    if (!errors) return;
    Object.entries(errors).forEach(([name, msgs]) => {
      const input = form.querySelector(`[name="${name}"]`);
      const err = form.querySelector(`.field-error[data-err="${name}"]`);
      const msg = Array.isArray(msgs) ? msgs[0] : String(msgs);
  
      if (input) input.classList.add("is-invalid");
      if (err) {
        err.textContent = msg;
        err.classList.add("show");
      }
    });
  }
  
  document.addEventListener("DOMContentLoaded", () => {
    closePanel();
    initPanZoom();
    requestAnimationFrame(refitMap);
    bindSvgLots();
  
    document.getElementById("panelClose")?.addEventListener("click", (e) => {
      e.preventDefault();
      closePanel();
      requestAnimationFrame(refitMap);
    });
  
    const form = document.getElementById("quoteForm");
    const btn = document.getElementById("quoteBtn");
  
    const phone = document.getElementById("quotePhone");
    const nameInput = document.getElementById("quoteName");
    const lastNameInput = document.getElementById("quoteLastName");
  
    if (phone) {
      phone.addEventListener("input", () => {
        phone.value = phone.value.replace(/[^\d+\-\s()]/g, "");
      });
    }
  
    const onlyLetters = (el) => {
      if (!el) return;
      el.addEventListener("input", () => {
        el.value = el.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, "");
      });
    };
    onlyLetters(nameInput);
    onlyLetters(lastNameInput);
  
    if (!form || !btn) return;
  
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearFieldErrors(form);
  
      const lotInput = document.getElementById("quoteLotCode");
      const lot = lotInput?.value?.trim();
      if (!lot) {
        showToast("Primero selecciona un lote.", false);
        return;
      }
  
      const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
      const fd = new FormData(form);
  
      const prev = btn.textContent;
      btn.textContent = "Enviando...";
      btn.disabled = true;
  
      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: { "X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest" },
          body: fd,
        });
  
        let data = {};
        try { data = await res.json(); } catch (e) { data = {}; }
  
        if (!res.ok) {
          const first =
            data?.errors?.telefono?.[0] ||
            data?.errors?.email?.[0] ||
            data?.errors?.id_lote?.[0] ||
            data?.message ||
            "Revisa los campos marcados.";
  
          applyFieldErrors(form, data.errors);
          showToast(first, false);
          return;
        }
  
        showToast("¡Gracias! Nos pondremos en contacto contigo pronto.", true);
        form.reset();
        lotInput.value = lot;
  
      } catch (err) {
        showToast("No pudimos enviar tu solicitud. Intenta más tarde.", false);
      } finally {
        btn.textContent = prev;
        btn.disabled = false;
      }
    });
  });
  