document.addEventListener("DOMContentLoaded", () => {
  // =========================
  // Helpers
  // =========================
  const $ = (sel, root = document) => root.querySelector(sel);

  const money = (n) => {
    if (n === null || n === undefined || n === "") return "—";
    const v = Number(n);
    if (Number.isNaN(v)) return "—";
    return v.toLocaleString("es-MX", { style: "currency", currency: "MXN" });
  };

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value ?? "—";
  };

  function normalizeLotId(raw) {
    if (!raw) return null;
    const s = String(raw).trim().toUpperCase();

    // MZ04-L01, MZ04-L1, MZ04-L001 -> MZ04-L01
    const m = s.match(/^MZ(\d{2})-L0*(\d{1,3})$/i);
    if (m) return `MZ${m[1]}-L${String(Number(m[2])).padStart(2, "0")}`;

    if (/^MZ\d{2}-L\d{2}$/i.test(s)) return s;

    return null;
  }

  // =========================
  // Toast (usa tu HTML: #quoteToast y #quoteToastMsg)
  // =========================
  let toastTimer = null;

  function showToast(msg, ok = false) {
    const toast = document.getElementById("quoteToast");
    const span = document.getElementById("quoteToastMsg");
    if (!toast || !span) return;

    span.textContent = msg || "";
    toast.hidden = false;

    toast.classList.toggle("is-success", !!ok);
    toast.classList.toggle("is-error", !ok);

    // por si tu CSS no maneja hidden/display:
    toast.style.display = "block";

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.hidden = true;
      toast.style.display = "none";
    }, 4200);
  }

  // =========================
  // Errores en campos (pinta inputs)
  // =========================
  function clearFieldErrors(form) {
    if (!form) return;
    form.querySelectorAll(".field-error").forEach((n) => n.remove());
    form.querySelectorAll(".has-error").forEach((n) => n.classList.remove("has-error"));
  }

  function applyFieldErrors(form, errors) {
    if (!form || !errors) return;

    Object.entries(errors).forEach(([name, msgs]) => {
      const input =
        form.querySelector(`[name="${name}"]`) ||
        document.getElementById(`quote${name[0]?.toUpperCase()}${name.slice(1)}`);

      if (!input) return;

      input.classList.add("has-error");

      const first = Array.isArray(msgs) ? msgs[0] : String(msgs);
      const err = document.createElement("div");
      err.className = "field-error";
      err.textContent = first;

      input.insertAdjacentElement("afterend", err);
    });
  }

  // =========================
  // Panel open/close
  // =========================
  function openPanel() {
    const root = document.getElementById("cotizador");
    if (!root) return;
    root.classList.remove("is-panel-closed");
  }

  function closePanel() {
    const root = document.getElementById("cotizador");
    if (!root) return;
    root.classList.add("is-panel-closed");
  }

  // Si tienes botón "Cerrar"
  const closeBtn = document.getElementById("panelClose");
  if (closeBtn) closeBtn.addEventListener("click", closePanel);

  // =========================
  // SVG Pan Zoom
  // =========================
  let panZoomInstance = null;

  function getSvgEl() {
    return document.querySelector("#mapWrap svg");
  }
  

  function refitMap() {
    if (!panZoomInstance) return;
    panZoomInstance.resize();
    panZoomInstance.fit();
    panZoomInstance.center();
  }

  function initPanZoom() {
    const svg = getSvgEl();
    if (!svg || typeof window.svgPanZoom !== "function") return;

    panZoomInstance = window.svgPanZoom(svg, {
      controlIconsEnabled: true,
      zoomEnabled: true,
      panEnabled: true,
      fit: true,
      center: true,
      minZoom: 0.5,
      maxZoom: 30,
      zoomScaleSensitivity: 0.25,
      dblClickZoomEnabled: false,
    });

    refitMap();
    window.addEventListener("resize", refitMap, { passive: true });
  }

  initPanZoom();

  // =========================
  // Lotes: estado -> color/clase, bloquear click y tooltip
  // =========================
  const lotStateById = new Map(); // id_lote -> estado

  function stateLabel(estadoRaw) {
    const s = String(estadoRaw || "").toLowerCase().trim();
    if (s === "vendido") return "VENDIDO";
    if (s === "apartado") return "APARTADO";
    return ""; // disponible u otro
  }

  function applyLotState(el, estadoRaw) {
    if (!el) return;
    const estado = String(estadoRaw || "").toLowerCase().trim();
    el.dataset.estado = estado;

    el.classList.remove("lot-status-vendido", "lot-status-apartado", "lot-status-disponible");

    if (estado === "vendido") el.classList.add("lot-status-vendido");
    else if (estado === "apartado") el.classList.add("lot-status-apartado");
    else el.classList.add("lot-status-disponible");

    const label = stateLabel(estado);
    if (label) {
      el.style.cursor = "not-allowed";
      el.setAttribute("title", label);
    } else {
      el.style.cursor = "pointer";
      el.removeAttribute("title");
    }
  }

  const lotBadge = document.getElementById("lotBadge");
const lotBadgeText = document.getElementById("lotBadgeText");

function showLotBadge(label, estado, clientX, clientY) {
  if (!lotBadge || !lotBadgeText) return;

  lotBadgeText.textContent = label;
  lotBadge.hidden = false;

  lotBadge.classList.remove("is-vendido", "is-apartado");
  if (estado === "vendido") lotBadge.classList.add("is-vendido");
  if (estado === "apartado") lotBadge.classList.add("is-apartado");

  lotBadge.style.left = `${clientX}px`;
  lotBadge.style.top = `${clientY}px`;
}

function hideLotBadge() {
  if (!lotBadge) return;
  lotBadge.hidden = true;
}


  async function fetchLot(id) {
    const res = await fetch(`/api/lote/${encodeURIComponent(id)}/`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return null;
    return data?.result || null;
  }

  async function loadLotIntoPanel(id) {
    const r = await fetchLot(id);
    if (!r) return;

    // Actualiza estado en mapa + pinta el lote
    lotStateById.set(id, String(r.estado_lote || "").toLowerCase().trim());

    // Título/panel
    setText("panelTitle", `${r.id_lote} — ${String(r.estado_lote || "").toUpperCase()}`);
    setText("kvCodigo", r.id_lote);
    setText("kvPrecio", money(r.precio_total));
    setText("kvProyecto", r.proyecto);
    setText("kvManzana", r.manzana);
    setText("kvArea", r.superficie_m2);
    setText("kvPm2", money(r.precio_m2));
    setText("kvMedidas", r.medidas_lotes);
    setText("kvApartado", money(r.cantidad_de_apartado));

    // Si tienes también estos (soporta nombres distintos desde la BD / API):
    const pick = (...keys) => {
      for (const k of keys) {
        const v = r?.[k];
        if (v !== null && v !== undefined && v !== "") return v;
      }
      return null;
    };

    const dias = pick("dias_limite_apartado", "dias_limite");
    if (document.getElementById("kvDiasLimite")) setText("kvDiasLimite", dias);
    if (document.getElementById("kvDias")) setText("kvDias", dias);

    // Tabla financiamiento si existe en tu HTML (acepta: cantidad_* / pago_* / nombres cortos):
    const enganche = pick("cantidad_enganche", "enganche");
    const financiamiento = pick("cantidad_financiamiento", "financiamiento");
    const mensualidad = pick("pago_mensualidad", "mensualidad");
    const liquidacion = pick("cantidad_liquidacion", "liquidacion");

    if (document.getElementById("kvEnganche")) setText("kvEnganche", money(enganche));
    if (document.getElementById("kvFinanciamiento")) setText("kvFinanciamiento", money(financiamiento));
    if (document.getElementById("kvMensualidad")) setText("kvMensualidad", money(mensualidad));
    if (document.getElementById("kvLiquidacion")) setText("kvLiquidacion", money(liquidacion));

    // Si tu panel usa IDs "fin*" (como en cotizador.js), también los llenamos:
    if (document.getElementById("finEnganche")) setText("finEnganche", money(enganche));
    if (document.getElementById("finFin")) setText("finFin", money(financiamiento));
    if (document.getElementById("finMens")) setText("finMens", money(mensualidad));
    if (document.getElementById("finLiq")) setText("finLiq", money(liquidacion));

    // Mantener el id_lote en hidden
    const lotInput =
      document.getElementById("quoteLotCode") ||
      document.getElementById("quoteLotId") ||
      document.querySelector('input[name="id_lote"]');

    if (lotInput) lotInput.value = r.id_lote;

        // =========================
    // Imagen del lote (PNG)
    // =========================
    const img = document.getElementById("lotImg");

    function lotImgUrl(lotId) {
      const s = String(lotId || "").trim().toUpperCase();

      // Caso: MZ04-L01 => carpeta MZ-04, archivo MZ04-L01.png
      const m = s.match(/^MZ(\d{2})-L(\d{2})$/);
      if (m) return `/static/resources/images/lots/MZ-${m[1]}/${s}.png`;

      // Fallback: sin carpeta (por si también tienes imágenes planas)
      return `/static/resources/images/lots/${s}.png`;
    }

    if (img) {
      const url = lotImgUrl(r.id_lote);
      img.src = url;
      img.alt = `Imagen del lote ${r.id_lote}`;

      img.onerror = () => {
        img.removeAttribute("src");
        img.alt = "Imagen no disponible";
      };
    }

  }

  function getLotElements() {
    const svg = getSvgEl();
    if (!svg) return [];

    // Si tus lotes son paths/rects con id tipo "MZ04-L01"
    const candidates = Array.from(svg.querySelectorAll("[id]"));
    return candidates.filter((el) => normalizeLotId(el.id) === el.id.toUpperCase());
  }

  const lotEls = getLotElements();
  lotEls.forEach((el) => el.classList.add("lot-hover"));
  lotEls.forEach((el) => {
    el.addEventListener("mouseenter", (e) => {
      const id = normalizeLotId(el.id);
      if (!id) return;
  
      const estado = lotStateById.get(id);
      if (estado !== "vendido" && estado !== "apartado") return;
  
      const label = estado === "vendido" ? "VENDIDO" : "APARTADO";
      showLotBadge(label, estado, e.clientX, e.clientY);
    });
  
    el.addEventListener("mousemove", (e) => {
      const id = normalizeLotId(el.id);
      if (!id) return;
  
      const estado = lotStateById.get(id);
      if (estado !== "vendido" && estado !== "apartado") return;
  
      const label = estado === "vendido" ? "VENDIDO" : "APARTADO";
      showLotBadge(label, estado, e.clientX, e.clientY);
    });
  
    el.addEventListener("mouseleave", () => {
      hideLotBadge();
    });
  
    el.addEventListener("click", async (e) => {
      e.preventDefault();
  
      const id = normalizeLotId(el.id);
      if (!id) return;
  
      const estado = lotStateById.get(id);
  
      if (estado === "vendido" || estado === "apartado") {
        showToast(`Este lote está ${estado}.`, false);
        return;
      }
  
      // ... tu lógica normal de cargar panel SOLO si disponible
    });
  });
  

  // Prefetch estados (son pocos lotes; esto permite tooltip sin click)
  (async () => {
    // pequeña concurrencia para no saturar
    const queue = [...lotEls];
    const workers = new Array(5).fill(0).map(async () => {
      while (queue.length) {
        const el = queue.shift();
        const id = el?.id;
        if (!id) continue;

        const r = await fetchLot(id);
        if (!r) continue;

        const estado = String(r.estado_lote || "").toLowerCase().trim();
        lotStateById.set(id, estado);
        applyLotState(el, estado);
      }
    });

    await Promise.all(workers);
  })();

  // Click en lote
  lotEls.forEach((el) => {
    el.addEventListener("click", async (e) => {
      e.preventDefault();

      const id = normalizeLotId(el.id);
      if (!id) return;

      // estado conocido (prefetch) o vacío
      const estado = lotStateById.get(id);

      // Si ya sabemos que NO está disponible => bloquear panel
      if (estado === "vendido" || estado === "apartado") {
        showToast(`Este lote está ${stateLabel(estado).toLowerCase()}.`, false);
        return;
      }

      // Si no sabemos, lo consultamos antes de abrir panel
      const r = await fetchLot(id);
      if (!r) return;

      const estadoNow = String(r.estado_lote || "").toLowerCase().trim();
      lotStateById.set(id, estadoNow);
      applyLotState(el, estadoNow);

      if (estadoNow === "vendido" || estadoNow === "apartado") {
        showToast(`Este lote está ${stateLabel(estadoNow).toLowerCase()}.`, false);
        return;
      }

      // Disponible => abrir panel y cargar info
      await loadLotIntoPanel(id);
      openPanel();

      // Selección visual
      document.querySelectorAll(".lot-selected").forEach((n) => n.classList.remove("lot-selected"));
      el.classList.add("lot-selected");
    });
  });

  // =========================
  // Form Cotización (AJAX)
  // =========================
  const form = document.getElementById("quoteForm");
  const btn = document.getElementById("quoteBtn");

  const phone =
    document.getElementById("quotePhone") ||
    (form ? form.querySelector('input[name="telefono"]') : null);

  const nameInput =
    document.getElementById("quoteName") ||
    (form ? form.querySelector('input[name="nombre"]') : null);

  const lastNameInput =
    document.getElementById("quoteLastName") ||
    (form ? form.querySelector('input[name="apellido"]') : null);

  // Tel: bloquear letras (deja dígitos, espacios, +, -, (, ))
  if (phone) {
    phone.setAttribute("inputmode", "tel");
    phone.addEventListener("input", () => {
      phone.value = phone.value.replace(/[^\d+\-\s()]/g, "");
    });
  }

  // Nombre/Apellido: bloquear números (deja letras, acentos, espacios, ', -)
  const cleanName = (v) =>
    String(v || "")
      .replace(/[0-9]/g, "")
      .replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'\-]/g, "");

  if (nameInput) {
    nameInput.addEventListener("input", () => {
      nameInput.value = cleanName(nameInput.value);
    });
  }

  if (lastNameInput) {
    lastNameInput.addEventListener("input", () => {
      lastNameInput.value = cleanName(lastNameInput.value);
    });
  }

  if (form && btn) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearFieldErrors(form);

      const lotInput =
        document.getElementById("quoteLotCode") ||
        document.getElementById("quoteLotId") ||
        form.querySelector('input[name="id_lote"]');

      const lot = lotInput?.value?.trim();
      if (!lot) {
        showToast("Primero selecciona un lote.", false);
        return;
      }

      const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
      const fd = new FormData(form);

      const prevText = btn.textContent;
      btn.textContent = "Enviando...";
      btn.disabled = true;

      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrf,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: fd,
        });

        let data = {};
        try {
          data = await res.json();
        } catch (_) {
          data = {};
        }

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
        // conservar lote
        if (lotInput) lotInput.value = lot;

      } catch (err) {
        showToast("No pudimos enviar tu solicitud. Intenta más tarde.", false);
      } finally {
        btn.textContent = prevText;
        btn.disabled = false;
      }
    });
  }
});
