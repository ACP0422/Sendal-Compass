
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

// Toast (usa tu HTML: #quoteToast y #quoteToastMsg)
// =========================
let toastTimer = null;

function showToast(msg, ok = false) {
  const box = document.getElementById("quoteMsgBox");
  if (!box) return;

  box.textContent = msg || "";

  box.className = "msg";

  if (ok) {
    box.classList.add("success");
  } else {
    box.classList.add("info");
  }

  box.style.display = "block";

  if (window.toastTimer) clearTimeout(window.toastTimer);

  window.toastTimer = setTimeout(() => {
    box.style.display = "none";
  }, 4500);
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
  
    // 🔄 limpiar mensaje anterior (proximamente / errores, etc.)
    const box = document.getElementById("quoteMsgBox");
    if (box) {
      box.style.display = "none";
      box.textContent = "";
      box.className = "msg"; // deja solo la clase base
    }
    if (window.toastTimer) {
      clearTimeout(window.toastTimer);
      window.toastTimer = null;
    }
  
    root.classList.remove("is-panel-closed");
  
    // 🔒 bloquear scroll del fondo
    document.body.classList.add("modal-open");
  }
  
  
  function closePanel() {
    const root = document.getElementById("cotizador");
    if (!root) return;
  
    root.classList.add("is-panel-closed");
  
    // 🔓 permitir scroll otra vez
    document.body.classList.remove("modal-open");
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
      mouseWheelZoomEnabled: true,     // scroll en desktop
      preventMouseEventsDefault: true, // que la lib controle los gestos
    });
  
    // 👉 Esto es clave para que el pinch funcione bien en móviles
    svg.addEventListener(
      "touchmove",
      function (e) {
        e.preventDefault();            // evita que el navegador haga scroll
      },
      { passive: false }
    );
  
    refitMap();
    window.addEventListener("resize", refitMap, { passive: true });
  }
  

  initPanZoom();

  // Etapas completas "PRÓXIMAMENTE" (todas menos MZ-04)
const PROX_STAGE_IDS = ["MZ-01", "MZ-02", "MZ-03", "MZ-05", "MZ-06", "MZ-07"];

function getStageIdFromLot(el) {
  if (!el) return null;
  const g = el.closest('g[id^="MZ-"]');
  return g ? g.id : null;
}


  // =========================
  // Lotes: estado -> color/clase, bloquear click y tooltip
  // =========================
  const lotStateById = new Map(); // id_lote -> estado

  function stateLabel(estadoRaw) {
    const s = String(estadoRaw || "").toLowerCase().trim();
    const labels = window.LOT_STATE_LABELS || {};
    return labels[s] || labels.disponible || "";
  }
  

  function applyLotState(el, estadoRaw) {
    if (!el) return;
  
    const estado = String(estadoRaw || "").toLowerCase().trim();
    el.dataset.estado = estado;
  
    // Limpia clases anteriores
    el.classList.remove(
      "lot-status-vendido",
      "lot-status-apartado",
      "lot-status-disponible",
      "lot-status-proximamente"
    );
  
    // Aplica clase de color según estado
    if (estado === "vendido") {
      el.classList.add("lot-status-vendido");
    } else if (estado === "apartado") {
      el.classList.add("lot-status-apartado");
    } else if (estado === "proximamente") {
      el.classList.add("lot-status-proximamente");
    } else {
      // cualquier otro => disponible
      el.classList.add("lot-status-disponible");
    }
  
    // Tooltip (title) a partir del mapa de labels traducibles
    const label = stateLabel(estado);
    if (label) {
      el.setAttribute("title", label);
    } else {
      el.removeAttribute("title");
    }
  
    // 🔑 Cursor solo bloqueado para NO disponibles
    const isNoDisponible =
      estado === "vendido" ||
      estado === "apartado" ||
      estado === "proximamente";
  
    if (isNoDisponible) {
      el.style.cursor = "not-allowed";
    } else {
      // disponibles y otros: se pueden clicar
      el.style.cursor = "pointer";
    }
  }
  

  const lotBadge = document.getElementById("lotBadge");
const lotBadgeText = document.getElementById("lotBadgeText");

function showLotBadge(label, estado, clientX, clientY) {
  if (!lotBadge || !lotBadgeText) return;

  lotBadgeText.textContent = label;
  lotBadge.hidden = false;

  lotBadge.classList.remove("is-vendido", "is-apartado", "is-proximamente");
  if (estado === "vendido") lotBadge.classList.add("is-vendido");
  if (estado === "apartado") lotBadge.classList.add("is-apartado");
  if (estado === "proximamente") lotBadge.classList.add("is-proximamente");

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
  
      // 👉 si es proximamente y NO es MZ-04 → NO mostrar por lote
      if (estado === "proximamente") {
        const stageId = getStageIdFromLot(el);
        if (stageId !== "MZ-04") return;
      }
  
      if (estado !== "vendido" && estado !== "apartado" && estado !== "proximamente")
        return;
      
      const label = stateLabel(estado);   // 👈 usa el mapa traducible
      
      showLotBadge(label, estado, e.clientX, e.clientY);
      
    });
  
    el.addEventListener("mousemove", (e) => {
      const id = normalizeLotId(el.id);
      if (!id) return;
  
      const estado = lotStateById.get(id);
  
      if (estado === "proximamente") {
        const stageId = getStageIdFromLot(el);
        if (stageId !== "MZ-04") return;
      }
  
      if (estado !== "vendido" && estado !== "apartado" && estado !== "proximamente")
        return;
      
      const label = stateLabel(estado);   // 👈 usa el mapa traducible
      
      showLotBadge(label, estado, e.clientX, e.clientY);
      
    });
  
    el.addEventListener("mouseleave", () => {
      hideLotBadge();
    });
  });

  
  function setupProximamenteStages() {
    if (!lotBadge || !lotBadgeText) return;
  
    PROX_STAGE_IDS.forEach((stageId) => {
      const stageEl = document.getElementById(stageId);
      if (!stageEl) return;
  
      stageEl.addEventListener("mouseenter", (e) => {
        showLotBadge("PRÓXIMAMENTE", "proximamente", e.clientX, e.clientY);
      });
  
      stageEl.addEventListener("mousemove", (e) => {
        // badge
        showLotBadge(
          stateLabel("proximamente"),
          "proximamente",
          e.clientX,
          e.clientY
        );
      
        // 👇 cursor prohibido
        mapWrap.style.cursor = "not-allowed";
      });
      
      stageEl.addEventListener("mouseleave", (e) => {
        hideLotBadge();
      
        // 👇 restaurar
        mapWrap.style.cursor = "default";
      });
      
    });
  }
  


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


  function stateToast(estadoRaw) {
    const s = String(estadoRaw || "").toLowerCase().trim();
    const messages = window.LOT_STATE_TOAST || {};
    return messages[s] || messages.disponible || "";
  }
  

   // Click / tap en lote (desktop + móvil + tableta)
   lotEls.forEach((el) => {
    const handleLotTap = async (e) => {
      // para que en móvil no haga zoom raro ni pase el evento al pan/zoom
      e.preventDefault();
      e.stopPropagation();

      const id = normalizeLotId(el.id);
      if (!id) return;

      // estado conocido (prefetch) o vacío
      const estado = lotStateById.get(id);

      // Si ya sabemos que NO está disponible => bloquear panel
      if (estado === "vendido" || estado === "apartado" || estado === "proximamente") {
        showToast(stateToast(estado), false);
        return;
      }

      // Si no sabemos, lo consultamos antes de abrir panel
      const r = await fetchLot(id);
      if (!r) return;

      const estadoNow = String(r.estado_lote || "").toLowerCase().trim();
      lotStateById.set(id, estadoNow);
      applyLotState(el, estadoNow);

      if (estadoNow === "vendido" || estadoNow === "apartado" || estadoNow === "proximamente") {
        showToast(stateToast(estadoNow), false);
        return;
      }

      // Disponible => abrir panel y cargar info
      await loadLotIntoPanel(id);
      openPanel();

      // Selección visual
      document
        .querySelectorAll(".lot-selected")
        .forEach((n) => n.classList.remove("lot-selected"));
      el.classList.add("lot-selected");
    };

    // Desktop
    el.addEventListener("click", handleLotTap);

    // Móvil / tableta
    el.addEventListener(
      "touchend",
      (e) => {
        handleLotTap(e);
      },
      { passive: false }
    );
  });


  setupProximamenteStages(); 

  // =========================
// Form Cotización (AJAX)
// =========================




// Limpia mensajes de error debajo de inputs
function clearFieldErrors(form) {
  form.querySelectorAll(".field-error").forEach((el) => {
    el.textContent = "";
    el.classList.remove("show");
  });

  form.querySelectorAll(".quote-field input").forEach((inp) => {
    inp.classList.remove("is-invalid");
  });
}

// Pone mensajes de error en los campos
function applyFieldErrors(form, errors) {
  if (!errors) return;

  Object.entries(errors).forEach(([field, msgs]) => {
    const msg = Array.isArray(msgs) ? msgs[0] : String(msgs);

    const input = form.querySelector(`[name="${field}"]`);
    if (input) {
      input.classList.add("is-invalid");
    }

    const err = form.querySelector(`.field-error[data-err="${field}"]`);
    if (err) {
      err.textContent = msg;
      err.classList.add("show");
    }
  });
}

// Elementos del formulario
const form = document.getElementById("quoteForm");
const btn = document.getElementById("quoteBtn");
const lotCodeInput = document.getElementById("quoteLotCode");

// =========================
// Validaciones frontend básicas
// =========================
if (form) {
  // --- Nombre y apellido: solo letras, espacios y guiones ---
  const onlyLettersRe = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s-]/g;

  const nameInputs = [
    document.getElementById("quoteName"),
    document.getElementById("quoteLastName"),
  ].filter(Boolean);

  nameInputs.forEach((el) => {
    // Elimina números y símbolos al vuelo
    el.addEventListener("input", () => {
      el.value = el.value
        .replace(onlyLettersRe, "")   // quita lo que no sea letra/espacio/guion
        .replace(/\s{2,}/g, " ");     // comprime espacios
    });

    // Limpia espacios al final
    el.addEventListener("blur", () => {
      el.value = el.value.trim();
    });
  });

  // --- Teléfono: no permitir letras ---
  const phoneInput =
    document.getElementById("quotePhone") ||
    form.querySelector('input[name="telefono"]');

  if (phoneInput) {
    phoneInput.setAttribute("inputmode", "tel");

    phoneInput.addEventListener("input", () => {
      // Solo dígitos y símbolos típicos de teléfono; sin letras
      phoneInput.value = phoneInput.value.replace(/[^0-9+\s\-()]/g, "");
    });

    phoneInput.addEventListener("blur", () => {
      phoneInput.value = phoneInput.value.trim();
    });
  }
}


if (form && btn) {
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearFieldErrors(form);

    // 1) Validar que haya lote seleccionado
    const lotInput =
      lotCodeInput ||
      form.querySelector("#quoteLotId") ||
      form.querySelector('input[name="id_lote"]');

    const lot = (lotInput?.value || "").trim();
    if (!lot) {
      showToast("Primero selecciona un lote.", false);
      return;
    }

    // 2) Tomar CSRF del input hidden de Django
    const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput ? csrfInput.value : null;

    // 3) Armar FormData
    const fd = new FormData(form);

    // 4) Deshabilitar botón y mostrar "Enviando..."
    const prevText = btn.textContent;
    btn.textContent = "Enviando...";
    btn.disabled = true;

    try {
      // 5) Enviar fetch con CSRF
      const res = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: fd,
      });

      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = {};
      }

      // 6) Si hay error (HTTP o de validación)
      if (!res.ok || data.errors) {
        applyFieldErrors(form, data.errors || {});

        const first =
          data?.errors?.telefono?.[0] ||
          data?.errors?.email?.[0] ||
          data?.errors?.nombre?.[0] ||
          data?.errors?.apellido?.[0] ||
          data?.errors?.id_lote?.[0] ||
          data?.message ||
          gettext("Revisa los campos marcados en rojo.");  // 👈 aquí

        showToast(first, false);
        return;
      }

      // 7) Éxito
      showToast(
        gettext("¡Gracias! Nos pondremos en contacto contigo pronto."), // 👈 aquí
        true
      );

     // Dejar el formulario limpio, pero mantener el id_lote por si quieres
    form.reset();
    if (lotInput) lotInput.value = lot;
    } catch (err) {
      // Error de red u otro
      showToast(
        gettext("No se pudo enviar tu solicitud. Inténtalo de nuevo."), // 👈 aquí
        false
      );
    } finally {
      // 8) Restaurar botón
      btn.textContent = prevText;
      btn.disabled = false;
    }
  });
}

});
