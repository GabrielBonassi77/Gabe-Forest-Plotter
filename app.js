const DEFAULT_ROWS = [
  ["Chronic Bronchitis", 1.31, 1.18, 1.45],
  ["COPD Exacerbation", 1.48, 1.33, 1.64],
  ["Lung Cancer", 2.96, 2.60, 3.33],
  ["Ischemic Stroke", 1.27, 1.14, 1.40],
  ["Myocardial Infarction", 1.34, 1.21, 1.48],
  ["Peripheral Artery Disease", 1.52, 1.36, 1.69],
  ["Pneumonia", 1.22, 1.10, 1.35],
  ["Hospitalization", 1.41, 1.27, 1.56],
  ["ICU Admission", 1.18, 1.06, 1.31],
  ["All Cause Mortality", 1.67, 1.50, 1.86],
].map(([outcome, mid, lo, hi]) => ({ outcome, mid, lo, hi }));

const els = {};
const state = {
  rows: structuredClone(DEFAULT_ROWS),
  lastValidAxis: { min: 0.5, max: 4 },
};

document.addEventListener("DOMContentLoaded", () => {
  [
    "effectMeasure", "exportDpi", "axisMin", "axisMax", "leftTicks", "rightTicks",
    "tableWidth", "fontSize", "markerSize", "figureWidth", "rowSpacing",
    "forestPlot", "dataBody", "plotFrame", "statusText", "fileInput",
    "tableWidthValue", "fontSizeValue", "markerSizeValue", "figureWidthValue", "rowSpacingValue",
    "loadExampleBtn", "downloadPngTopBtn", "resetAxisBtn", "downloadPdfBtn",
    "downloadPngBtn", "downloadTiffBtn", "downloadSvgBtn", "templateBtn", "addRowBtn",
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });

  renderTable();
  bindEvents();
  renderPlot();
});

function bindEvents() {
  document.querySelectorAll("input, select").forEach((control) => {
    control.addEventListener("input", () => {
      updateSliderLabels();
      renderPlot();
    });
  });

  document.querySelectorAll(".control-grid input").forEach((input) => {
    input.addEventListener("focus", () => {
      input.dataset.replaceNext = "true";
      requestAnimationFrame(() => input.select());
    });
    input.addEventListener("beforeinput", (event) => {
      if (input.dataset.replaceNext === "true" && event.inputType === "insertText") {
        input.value = "";
      }
      input.dataset.replaceNext = "false";
    });
  });

  els.resetAxisBtn.addEventListener("click", () => {
    els.axisMin.value = "0.5";
    els.axisMax.value = "4";
    els.leftTicks.value = "4";
    els.rightTicks.value = "2";
    state.lastValidAxis = { min: 0.5, max: 4 };
    renderPlot();
  });

  els.loadExampleBtn.addEventListener("click", () => {
    state.rows = structuredClone(DEFAULT_ROWS);
    renderTable();
    renderPlot();
    setStatus("Example data loaded.");
  });

  els.addRowBtn.addEventListener("click", () => {
    state.rows.push({ outcome: "New outcome", mid: 1.2, lo: 1.0, hi: 1.4 });
    renderTable();
    renderPlot();
  });

  els.templateBtn.addEventListener("click", () => {
    downloadBlob("forest-plot-template.csv", new Blob([toCsv(DEFAULT_ROWS)], { type: "text/csv" }));
  });

  els.fileInput.addEventListener("change", handleFile);
  els.downloadSvgBtn.addEventListener("click", downloadSvg);
  els.downloadPngBtn.addEventListener("click", () => downloadPng());
  els.downloadPngTopBtn.addEventListener("click", () => downloadPng());
  els.downloadPdfBtn.addEventListener("click", downloadPdf);
  els.downloadTiffBtn.addEventListener("click", downloadTiff);
}

function updateSliderLabels() {
  els.tableWidthValue.textContent = Number(els.tableWidth.value).toFixed(2);
  els.fontSizeValue.textContent = els.fontSize.value;
  els.markerSizeValue.textContent = els.markerSize.value;
  els.figureWidthValue.textContent = Number(els.figureWidth.value).toFixed(1);
  els.rowSpacingValue.textContent = Number(els.rowSpacing.value).toFixed(1).replace(".0", "");
}

function renderTable() {
  els.dataBody.textContent = "";
  state.rows.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.append(
      cellInput(index, "outcome", "text", row.outcome),
      cellInput(index, "mid", "number", row.mid),
      cellInput(index, "lo", "number", row.lo),
      cellInput(index, "hi", "number", row.hi),
      actionCell(index),
    );
    els.dataBody.appendChild(tr);
  });
}

function cellInput(index, key, type, value) {
  const td = document.createElement("td");
  const input = document.createElement("input");
  input.value = value;
  input.type = type;
  if (type === "number") input.step = "0.01";
  input.addEventListener("input", () => {
    state.rows[index][key] = type === "number" ? Number(input.value) : input.value;
    renderPlot();
  });
  td.appendChild(input);
  return td;
}

function actionCell(index) {
  const td = document.createElement("td");
  const button = document.createElement("button");
  button.className = "row-delete";
  button.type = "button";
  button.title = "Delete row";
  button.textContent = "×";
  button.addEventListener("click", () => {
    state.rows.splice(index, 1);
    renderTable();
    renderPlot();
  });
  td.appendChild(button);
  return td;
}

function validRows() {
  return state.rows
    .map((row) => ({
      outcome: String(row.outcome ?? "").trim(),
      mid: Number(row.mid),
      lo: Number(row.lo),
      hi: Number(row.hi),
    }))
    .filter((row) => row.outcome && [row.mid, row.lo, row.hi].every(Number.isFinite))
    .filter((row) => row.lo <= row.mid && row.mid <= row.hi);
}

function getConfig() {
  let min = Number(els.axisMin.value);
  let max = Number(els.axisMax.value);
  let warning = "";

  if (!Number.isFinite(min) || !Number.isFinite(max) || min <= 0 || max <= 0 || min >= max || !(min < 1 && 1 < max)) {
    warning = "Axis must be positive and keep 1 between min and max. Using last valid axis.";
    min = state.lastValidAxis.min;
    max = state.lastValidAxis.max;
  } else {
    state.lastValidAxis = { min, max };
  }

  return {
    effect: (els.effectMeasure.value.trim() || "HR").slice(0, 12),
    dpi: Number(els.exportDpi.value),
    min,
    max,
    leftTicks: clampInt(els.leftTicks.value, 0, 20),
    rightTicks: clampInt(els.rightTicks.value, 0, 20),
    tableWidth: Number(els.tableWidth.value),
    fontSize: Number(els.fontSize.value),
    markerSize: Number(els.markerSize.value),
    figureWidth: Number(els.figureWidth.value),
    rowSpacing: Number(els.rowSpacing.value),
    warning,
  };
}

function clampInt(value, min, max) {
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return min;
  return Math.max(min, Math.min(max, n));
}

function buildTicks(config) {
  const left = linspace(config.min, 1, config.leftTicks + 2);
  const right = linspace(1, config.max, config.rightTicks + 2).slice(1);
  const all = uniqueSorted([...left, ...right].map((v) => Number(v.toFixed(10))));
  const labels = uniqueSorted([config.min, 1, config.max].map((v) => Number(v.toFixed(10))));
  return {
    major: labels,
    minor: all.filter((tick) => !labels.some((label) => Math.abs(label - tick) < 1e-8)),
  };
}

function linspace(start, end, count) {
  if (count <= 1) return [start];
  return Array.from({ length: count }, (_, i) => start + ((end - start) * i) / (count - 1));
}

function uniqueSorted(values) {
  return [...new Set(values.map((v) => Number(v.toFixed(10))))].sort((a, b) => a - b);
}

function fmtTick(value) {
  return Math.abs(value - Math.round(value)) < 1e-8 ? String(Math.round(value)) : Number(value.toPrecision(3)).toString();
}

function renderPlot() {
  updateSliderLabels();
  const config = getConfig();
  const rows = validRows();
  const svg = els.forestPlot;
  svg.textContent = "";

  if (!rows.length) {
    setStatus("Add at least one complete row.");
    return;
  }

  const axisLabel = `${config.effect} (95% CI)`;
  const nRowsTotal = rows.length + 1;
  const width = Math.round(config.figureWidth * 96);
  const baseHeight = Math.round((nRowsTotal * config.rowSpacing) / 72 * 96 + 28);
  const bottomWhitespace = 38;
  const height = baseHeight + bottomWhitespace;
  const tableWidth = width * config.tableWidth;
  const plotWidth = width - tableWidth - 32;
  const leftPad = 18;
  const topPad = 14;
  const bottomPad = 30 + bottomWhitespace;
  const rowPitch = (height - topPad - bottomPad) / nRowsTotal;
  const plotX = tableWidth + 22;
  const plotYTop = topPad;
  const axisY = height - bottomPad + 2;
  const fontSize = config.fontSize;
  const ticks = buildTicks(config);

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.innerHTML = `<rect width="${width}" height="${height}" fill="#fff"></rect>`;

  addText(svg, leftPad, topPad + rowPitch * 0.56, "Outcome", fontSize, "bold");
  addText(svg, tableWidth * 0.55, topPad + rowPitch * 0.56, axisLabel, fontSize, "bold");
  addLine(svg, leftPad, topPad + rowPitch * 0.82, tableWidth - 8, topPad + rowPitch * 0.82, "#000", 1.2);

  const x = (value) => plotX + ((value - config.min) / (config.max - config.min)) * plotWidth;
  addLine(svg, x(1), plotYTop + 4, x(1), axisY, "#000", 1, "2 2");
  addLine(svg, plotX, axisY, plotX + plotWidth, axisY, "#222", 1);

  ticks.minor.forEach((tick) => addLine(svg, x(tick), axisY, x(tick), axisY + 4, "#222", 0.8));
  ticks.major.forEach((tick) => {
    addLine(svg, x(tick), axisY, x(tick), axisY + 6, "#222", 1);
    addText(svg, x(tick), axisY + 18, fmtTick(tick), fontSize, "normal", "middle");
  });
  addText(svg, plotX + plotWidth / 2, axisY + fontSize * 3, axisLabel, fontSize, "normal", "middle");

  rows.forEach((row, i) => {
    const y = topPad + rowPitch * (i + 1.55);
    addText(svg, leftPad, y, row.outcome, fontSize, "normal");
    addText(svg, tableWidth * 0.55, y, `${row.mid.toFixed(2)} (${row.lo.toFixed(2)}-${row.hi.toFixed(2)})`, fontSize, "normal");
    if (i < rows.length - 1) {
      addLine(svg, leftPad, y + rowPitch * 0.43, tableWidth - 8, y + rowPitch * 0.43, "rgba(0,0,0,0.25)", 0.8);
    }
    addLine(svg, x(row.lo), y - 1, x(row.hi), y - 1, "#4d4d4d", 1.6);
    addSquare(svg, x(row.mid), y - 1, Math.sqrt(config.markerSize) * 1.35);
  });

  setStatus(config.warning || "Ready");
}

function addText(svg, x, y, text, size, weight = "normal", anchor = "start") {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "text");
  node.setAttribute("x", x);
  node.setAttribute("y", y);
  node.setAttribute("fill", "#000");
  node.setAttribute("font-family", "Times New Roman, Times, serif");
  node.setAttribute("font-size", size);
  node.setAttribute("font-weight", weight);
  node.setAttribute("dominant-baseline", "middle");
  node.setAttribute("text-anchor", anchor);
  node.textContent = text;
  svg.appendChild(node);
}

function addLine(svg, x1, y1, x2, y2, color, width, dash = "") {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "line");
  node.setAttribute("x1", x1);
  node.setAttribute("y1", y1);
  node.setAttribute("x2", x2);
  node.setAttribute("y2", y2);
  node.setAttribute("stroke", color);
  node.setAttribute("stroke-width", width);
  if (dash) node.setAttribute("stroke-dasharray", dash);
  node.setAttribute("stroke-linecap", "butt");
  svg.appendChild(node);
}

function addSquare(svg, cx, cy, size) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  node.setAttribute("x", cx - size / 2);
  node.setAttribute("y", cy - size / 2);
  node.setAttribute("width", size);
  node.setAttribute("height", size);
  node.setAttribute("fill", "#335c66");
  node.setAttribute("stroke", "#1a2e33");
  node.setAttribute("stroke-width", 1.2);
  svg.appendChild(node);
}

async function handleFile(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  try {
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext === "csv") {
      const text = await file.text();
      state.rows = coerceRows(parseCsv(text));
    } else {
      if (!window.XLSX) throw new Error("Excel support is still loading. Try again in a moment.");
      const buffer = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: "array" });
      const first = workbook.Sheets[workbook.SheetNames[0]];
      state.rows = coerceRows(XLSX.utils.sheet_to_json(first, { defval: "" }));
    }
    renderTable();
    renderPlot();
    setStatus(`Loaded ${state.rows.length} row${state.rows.length === 1 ? "" : "s"} from ${file.name}.`);
  } catch (error) {
    setStatus(error.message || "Could not load file.");
  } finally {
    event.target.value = "";
  }
}

function parseCsv(text) {
  const rows = [];
  let current = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (ch === '"' && quoted && next === '"') {
      cell += '"';
      i += 1;
    } else if (ch === '"') {
      quoted = !quoted;
    } else if (ch === "," && !quoted) {
      current.push(cell);
      cell = "";
    } else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && next === "\n") i += 1;
      current.push(cell);
      rows.push(current);
      current = [];
      cell = "";
    } else {
      cell += ch;
    }
  }
  if (cell || current.length) {
    current.push(cell);
    rows.push(current);
  }
  const headers = rows.shift()?.map((h) => normalizeHeader(h)) ?? [];
  return rows.filter((row) => row.some((value) => String(value).trim())).map((row) => {
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = row[index] ?? "";
    });
    return obj;
  });
}

function normalizeHeader(header) {
  const key = String(header).trim().toLowerCase();
  const map = {
    outcome: "outcome",
    label: "outcome",
    mid: "mid",
    midpoint: "mid",
    "mid point": "mid",
    estimate: "mid",
    lo: "lo",
    lower: "lo",
    "low ci": "lo",
    lower_ci: "lo",
    hi: "hi",
    upper: "hi",
    "high ci": "hi",
    upper_ci: "hi",
  };
  return map[key] || key;
}

function coerceRows(rawRows) {
  const rows = rawRows.map((row) => {
    const normalized = {};
    Object.entries(row).forEach(([key, value]) => {
      normalized[normalizeHeader(key)] = value;
    });
    return {
      outcome: String(normalized.outcome ?? "").trim(),
      mid: Number(normalized.mid),
      lo: Number(normalized.lo),
      hi: Number(normalized.hi),
    };
  }).filter((row) => row.outcome && [row.mid, row.lo, row.hi].every(Number.isFinite));

  if (!rows.length) throw new Error("No complete rows found. Check your column names.");
  const invalidIndex = rows.findIndex((row) => row.lo > row.mid || row.mid > row.hi);
  if (invalidIndex >= 0) throw new Error(`Each row must satisfy Low CI <= Mid point <= High CI. Check row ${invalidIndex + 1}.`);
  return rows.slice(0, 50);
}

function toCsv(rows) {
  const escape = (value) => `"${String(value).replaceAll('"', '""')}"`;
  return [
    "Outcome,Mid point,Low CI,High CI",
    ...rows.map((row) => [row.outcome, row.mid, row.lo, row.hi].map(escape).join(",")),
  ].join("\n");
}

function svgBlob() {
  const clone = els.forestPlot.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  return new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml;charset=utf-8" });
}

function downloadSvg() {
  downloadBlob("forestpanel.svg", svgBlob());
}

async function svgToCanvas() {
  const blob = svgBlob();
  const url = URL.createObjectURL(blob);
  const image = new Image();
  const config = getConfig();
  const scale = Math.max(1, config.dpi / 96);
  try {
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
      image.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    return canvas;
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function downloadPng() {
  const canvas = await svgToCanvas();
  canvas.toBlob((blob) => downloadBlob("forestpanel.png", blob), "image/png");
}

async function downloadPdf() {
  if (!window.jspdf?.jsPDF) {
    setStatus("PDF library is still loading. Try again in a moment.");
    return;
  }
  const canvas = await svgToCanvas();
  const pdf = new window.jspdf.jsPDF({
    orientation: canvas.width >= canvas.height ? "landscape" : "portrait",
    unit: "pt",
    format: [canvas.width * 0.75, canvas.height * 0.75],
  });
  pdf.addImage(canvas.toDataURL("image/png"), "PNG", 0, 0, canvas.width * 0.75, canvas.height * 0.75);
  pdf.save("forestpanel.pdf");
}

async function downloadTiff() {
  if (!window.UTIF) {
    setStatus("TIFF library is still loading. Try again in a moment.");
    return;
  }
  const canvas = await svgToCanvas();
  const ctx = canvas.getContext("2d");
  const rgba = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const buffer = UTIF.encodeImage(rgba.buffer, canvas.width, canvas.height);
  downloadBlob("forestpanel.tiff", new Blob([buffer], { type: "image/tiff" }));
}

function downloadBlob(filename, blob) {
  if (!blob) return;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function setStatus(message) {
  els.statusText.textContent = message;
}
