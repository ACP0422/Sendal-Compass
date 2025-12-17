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
  
    // MZ04-L1 / MZ04-L01 / MZ04-L001  -> MZ04-L01
    const m = s.match(/^MZ(\d{2})-L0*(\d{1,3})$/i);
    if (m) return `MZ${m[1]}-L${String(Number(m[2])).padStart(2, "0")}`;
  
    // Si tu SVG trae exactamente MZ04-L01
    if (/^MZ\d{2}-L\d{2}$/i.test(s)) return s;
  
    return null;
  }
  
  async function loadLot(rawLotId) {
    const lotId = normalizeLotId(rawLotId);
    if (!lotId) {
      console.warn("No pude normalizar el lote:", rawLotId);
      return;
    }
  
    console.log("Consultando:", lotId);
  
    const res = await fetch(`/api/lote/${encodeURIComponent(lotId)}/`);
  
    let data = null;
    try { data = await res.json(); } catch (e) {}
  
    if (!res.ok) {
      console.warn("API no encontró lote:", lotId, data);
      return;
    }
  
    const r = data.result;
  
    setText("panelTitle", `${(r.id_lote)} — ${String(r.estado_lote || "").toUpperCase()}`);
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

    const panel = document.querySelector(".cotizador-panel");
    if (panel) panel.style.display = "";

  }
  
  
  function bindSvgLots() {
    const svg = document.querySelector("svg");
    if (!svg) return;
  
    const nodes = svg.querySelectorAll("[data-lot], [id]");
    nodes.forEach((el) => {
      const lotId = el.getAttribute("data-lot") || el.id;
      if (!lotId) return;
  
      // solo bind a los que sí parecen lote
      if (!normalizeLotId(lotId)) return;
  
      el.style.cursor = "pointer";
      el.addEventListener("click", () => loadLot(lotId));
    });
  }
  
  document.getElementById("panelClose")?.addEventListener("click", (e) => {
    e.preventDefault();
  
    const panel =
      document.querySelector(".cotizador-panel") ||
      document.getElementById("lotPanel") ||
      document.getElementById("infoPanel") ||
      document.querySelector(".lot-panel") ||
      document.querySelector("[data-lot-panel]");
  
    if (panel) panel.style.display = "none";
  });
  
  
  
  bindSvgLots();
  