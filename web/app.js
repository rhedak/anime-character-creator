// The web tool's whole JavaScript surface. Per CLAUDE.md and
// docs/web-gui-plan.md: this file learns no geometry and no character-model
// knowledge from anywhere but two committed files it fetches at runtime,
// ref-out/catalogue.json (which fields exist, their labels and ranges) and
// the package's own .py sources (which it hands to Pyodide unmodified). If a
// field name, a hairstyle, or a range shows up here as a literal, that is a
// bug: it belongs in catalogue.py instead, or this and the Python model can
// drift exactly the way a second implementation always does.
//
// The one thing that *is* a literal here is which .py files to fetch, since
// Pyodide's virtual filesystem has to be told what a package contains before
// it can import one.
"use strict";

const PACKAGE_FILES = [
  "__init__.py",
  "__main__.py",
  "character.py",
  "colorutil.py",
  "cover.py",
  "generate.py",
  "presets.py",
  "sheet.py",
  "skeleton.py",
  "catalogue.py",
  "urlstate.py",
  "attribution.py",
];

// The bridge: the only Python this file writes itself, and it does nothing
// `anime_character_creator` does not already do in `render_character`,
// `catalogue.build_catalogue` and `urlstate`. It exists so the JS side never
// has to serialize a CharacterParams by hand or reimplement the base64
// encoding urlstate.py already defines, which is the same no-second-copy
// reasoning `docs/web-gui-plan.md` gives for running the real package in the
// browser at all rather than porting it.
const BRIDGE_PY = `
import json as _json
from anime_character_creator import PRESETS, NEUTRAL_BASES, render_character
from anime_character_creator.urlstate import params_from_dict, params_to_dict, encode_params, decode_params

def _bridge_state_for_start(start_id):
    if start_id in PRESETS:
        p = PRESETS[start_id]
    elif start_id in NEUTRAL_BASES:
        p = NEUTRAL_BASES[start_id]
    else:
        raise ValueError(f"no such starting point: {start_id}")
    return _json.dumps(params_to_dict(p))

def _bridge_render(state_json, background, metadata):
    p = params_from_dict(_json.loads(state_json))
    return render_character(p, background=background, metadata=bool(metadata))

def _bridge_encode(state_json):
    p = params_from_dict(_json.loads(state_json))
    return encode_params(p)

def _bridge_decode(encoded):
    p = decode_params(encoded)
    return _json.dumps(params_to_dict(p))
`;

const statusEl = document.getElementById("status");
const gallerySection = document.getElementById("gallery-section");
const castGallery = document.getElementById("cast-gallery");
const baseGallery = document.getElementById("base-gallery");
const editorSection = document.getElementById("editor-section");
const previewEl = document.getElementById("preview");
const colorsControls = document.getElementById("colors-controls");
const hairControls = document.getElementById("hair-controls");
const faceControls = document.getElementById("face-controls");
const garmentsControls = document.getElementById("garments-controls");
const downloadSvgBtn = document.getElementById("download-svg");
const downloadPngBtn = document.getElementById("download-png");
const copyLinkBtn = document.getElementById("copy-link");
const copyLinkStatus = document.getElementById("copy-link-status");
const backButton = document.getElementById("back-to-gallery");

let catalogue = null;
let bridge = null; // { render, encode, decode, stateForStart }
let state = null; // plain object mirroring CharacterParams, once a start is picked

function setStatus(text, isError) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", Boolean(isError));
}

// --- Gallery: built from ref-out/catalogue.json alone, before Python exists.
// The cast gets its committed ref-out/<id>.svg, so this paints instantly, per
// "a character is on screen immediately" in docs/web-gui-plan.md. The two
// neutral bases get the same treatment from ref-out/bases/<id>.svg: a
// separate small directory rather than ref-out/'s top level, since
// NEUTRAL_BASES is deliberately not in PRESETS (see presets.py) and
// refresh-ref-out.sh and the README's per-character test both read PRESETS.
// refresh-bases.sh is the one script that knows the two exist.

function buildGallery() {
  for (const entry of catalogue.starting_points.cast) {
    castGallery.appendChild(galleryCard(entry, `ref-out/${entry.id}.svg`));
  }
  for (const entry of catalogue.starting_points.bases) {
    baseGallery.appendChild(galleryCard(entry, `ref-out/bases/${entry.id}.svg`));
  }
}

function galleryCard(entry, imgSrc) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "gallery-card";
  card.dataset.startId = entry.id;
  const img = document.createElement("img");
  img.src = imgSrc;
  img.alt = entry.label;
  img.loading = "lazy";
  card.appendChild(img);
  const label = document.createElement("div");
  label.textContent = entry.label;
  card.appendChild(label);
  card.disabled = true; // enabled once Pyodide is ready
  card.addEventListener("click", () => selectStartingPoint(entry.id));
  return card;
}

function enableGalleryCards() {
  for (const card of document.querySelectorAll(".gallery-card")) {
    card.disabled = false;
  }
}

// --- Controls, built from the catalogue schema plus whatever `state`
// currently holds. Rebuilt each time a starting point is picked, since a
// different starting point can turn different garment slots on.

function fieldValue(field) {
  if (field in state) return state[field];
  return state.outfit ? state.outfit[field] : undefined;
}

function setField(field, value) {
  if (field in state) {
    state[field] = value;
  } else {
    state.outfit[field] = value;
  }
}

function faceValue(field) {
  return state.face[field];
}

function setFaceField(field, value) {
  state.face[field] = value;
}

function colorRow(container, field, label, value, onInput) {
  const row = document.createElement("div");
  row.className = "control-row";
  const id = `field-${field}`;
  const lbl = document.createElement("label");
  lbl.htmlFor = id;
  lbl.textContent = label;
  const input = document.createElement("input");
  input.type = "color";
  input.id = id;
  input.value = value || "#8a8a8a";
  input.addEventListener("input", () => onInput(input.value));
  row.append(lbl, input);
  container.appendChild(row);
  return input;
}

function rangeRow(container, field, label, lo, hi, value, onInput) {
  const row = document.createElement("div");
  row.className = "control-row";
  const id = `field-${field}`;
  const lbl = document.createElement("label");
  lbl.htmlFor = id;
  lbl.textContent = label;
  const input = document.createElement("input");
  input.type = "range";
  input.id = id;
  input.min = String(lo);
  input.max = String(hi);
  input.step = "0.01";
  input.value = String(value === null || value === undefined ? (lo + hi) / 2 : value);
  input.addEventListener("input", () => onInput(Number(input.value)));
  row.append(lbl, input);
  container.appendChild(row);
  return input;
}

function selectRow(container, field, label, options, value, onInput) {
  const row = document.createElement("div");
  row.className = "control-row";
  const id = `field-${field}`;
  const lbl = document.createElement("label");
  lbl.htmlFor = id;
  lbl.textContent = label;
  const select = document.createElement("select");
  select.id = id;
  for (const opt of options) {
    const option = document.createElement("option");
    option.value = String(opt.value);
    option.textContent = opt.label;
    if (opt.value === value) option.selected = true;
    select.appendChild(option);
  }
  select.addEventListener("input", () => {
    const chosen = options.find((opt) => String(opt.value) === select.value);
    onInput(chosen.value);
  });
  row.append(lbl, select);
  container.appendChild(row);
  return select;
}

function boolRow(container, field, label, value, onInput) {
  const row = document.createElement("div");
  row.className = "control-row";
  const id = `field-${field}`;
  const lbl = document.createElement("label");
  lbl.htmlFor = id;
  lbl.textContent = label;
  const input = document.createElement("input");
  input.type = "checkbox";
  input.id = id;
  input.checked = Boolean(value);
  input.addEventListener("input", () => onInput(input.checked));
  row.append(input, lbl);
  container.appendChild(row);
  return input;
}

function buildColorControls() {
  colorsControls.innerHTML = "";
  for (const c of catalogue.colors) {
    if (c.field === "hair_tip_color") continue; // shown in the Hair section
    colorRow(colorsControls, c.field, c.label, fieldValue(c.field), (v) => {
      setField(c.field, v);
      scheduleRender();
    });
  }
}

function buildHairControls() {
  hairControls.innerHTML = "";

  const row = document.createElement("div");
  row.className = "control-row";
  const lbl = document.createElement("label");
  lbl.htmlFor = "field-hairstyle";
  lbl.textContent = "Cut";
  const select = document.createElement("select");
  select.id = "field-hairstyle";
  for (const h of catalogue.hairstyles) {
    const opt = document.createElement("option");
    opt.value = h.id;
    opt.textContent = h.label;
    if (h.id === state.hairstyle) opt.selected = true;
    select.appendChild(opt);
  }
  select.addEventListener("input", () => {
    state.hairstyle = select.value;
    scheduleRender();
  });
  row.append(lbl, select);
  hairControls.appendChild(row);

  rangeRow(
    hairControls,
    "hair_length",
    catalogue.hair_length.label,
    catalogue.hair_length.min,
    catalogue.hair_length.max,
    state.hair_length,
    (v) => {
      state.hair_length = v;
      scheduleRender();
    },
  );

  const tip = catalogue.colors.find((c) => c.field === "hair_tip_color");
  const tipRow = document.createElement("div");
  tipRow.className = "control-row";
  const tipCheckbox = boolRow(
    tipRow,
    "hair_tip_on",
    "Fade to a second colour at the ends",
    state.hair_tip_color !== null,
    (on) => {
      state.hair_tip_color = on ? state.hair_color : null;
      buildHairControls();
      scheduleRender();
    },
  );
  hairControls.appendChild(tipRow);
  if (tipCheckbox.checked) {
    colorRow(hairControls, tip.field, tip.label, state.hair_tip_color, (v) => {
      state.hair_tip_color = v;
      scheduleRender();
    });
  }

  rangeRow(
    hairControls,
    "hair_tail",
    catalogue.hair_tail.label,
    catalogue.hair_tail.min,
    catalogue.hair_tail.max,
    state.hair_tail,
    (v) => {
      state.hair_tail = v;
      scheduleRender();
    },
  );

  boolRow(hairControls, "hair_knot", catalogue.hair_knot.label, state.hair_knot, (v) => {
    state.hair_knot = v;
    scheduleRender();
  });
}

function buildFaceControls() {
  faceControls.innerHTML = "";
  for (const r of catalogue.face.ranges) {
    rangeRow(faceControls, r.field, r.label, r.min, r.max, faceValue(r.field), (v) => {
      setFaceField(r.field, v);
      scheduleRender();
    });
  }
  for (const b of catalogue.face.bools) {
    boolRow(faceControls, b.field, b.label, faceValue(b.field), (v) => {
      setFaceField(b.field, v);
      scheduleRender();
    });
  }
  const s = catalogue.face.select;
  selectRow(faceControls, s.field, s.label, s.options, faceValue(s.field), (v) => {
    setFaceField(s.field, v);
    scheduleRender();
  });
}

function buildGarmentControls() {
  garmentsControls.innerHTML = "";
  for (const g of catalogue.garments) {
    garmentsControls.appendChild(garmentBlock(g));
  }
  applyRequiresVisibility();
}

function garmentBlock(g) {
  const block = document.createElement("div");
  block.className = "garment-block";
  block.dataset.garmentId = g.id;

  const header = document.createElement("div");
  header.className = "control-row";

  const on = fieldValue(g.color.field) !== null;
  block.dataset.off = String(!on);

  if (g.color.optional) {
    boolRow(header, `${g.id}-on`, g.label, on, (checked) => {
      if (checked) {
        setField(g.color.field, "#8a8a8a");
        for (const r of g.ranges || []) {
          if (fieldValue(r.field) === null || fieldValue(r.field) === undefined) {
            setField(r.field, (r.lo + r.hi) / 2);
          }
        }
      } else {
        setField(g.color.field, null);
        turnOffDependents(g.id);
      }
      buildGarmentControls();
      scheduleRender();
    });
  } else {
    const lbl = document.createElement("span");
    lbl.textContent = g.label;
    header.appendChild(lbl);
  }
  block.appendChild(header);

  const details = document.createElement("div");
  details.className = "garment-details";
  colorRow(details, g.color.field, "Colour", fieldValue(g.color.field), (v) => {
    setField(g.color.field, v);
    scheduleRender();
  });
  for (const r of g.ranges || []) {
    const value = fieldValue(r.field);
    rangeRow(details, r.field, r.label, r.min, r.max, value, (v) => {
      setField(r.field, v);
      scheduleRender();
    });
  }
  for (const b of g.bools || []) {
    boolRow(details, b.field, b.label, fieldValue(b.field), (v) => {
      setField(b.field, v);
      scheduleRender();
    });
  }
  block.appendChild(details);
  return block;
}

function turnOffDependents(garmentId) {
  for (const g of catalogue.garments) {
    if (g.requires === garmentId && fieldValue(g.color.field) !== null) {
      setField(g.color.field, null);
      turnOffDependents(g.id);
    }
  }
}

function applyRequiresVisibility() {
  for (const g of catalogue.garments) {
    if (!g.requires) continue;
    const block = garmentsControls.querySelector(`[data-garment-id="${g.id}"]`);
    const requirementOn = fieldValue(garmentField(g.requires)) !== null;
    block.hidden = !requirementOn;
  }
}

function garmentField(garmentId) {
  const g = catalogue.garments.find((x) => x.id === garmentId);
  return g.color.field;
}

// --- Rendering. Pyodide runs synchronously once loaded, well under a
// millisecond per docs/web-gui-plan.md's own measurement, so a
// requestAnimationFrame coalesce is enough to keep a dragged slider smooth
// without a debounce timer.

let renderScheduled = false;
function scheduleRender() {
  if (renderScheduled) return;
  renderScheduled = true;
  requestAnimationFrame(() => {
    renderScheduled = false;
    renderPreview();
    updateAddressBar();
  });
}

function renderPreview() {
  if (!bridge || !state) return;
  const svg = bridge.render(JSON.stringify(state), null, false);
  previewEl.innerHTML = svg;
}

// The full shareable link for the current `state`: this page's own address
// (which, once deployed, is the tool's real URL) plus the encoded character.
// Used for the address bar, "Copy link", and the PNG's attribution text, so
// all three always agree with each other.
function shareUrl() {
  const encoded = bridge.encode(JSON.stringify(state));
  const url = new URL(window.location.href);
  url.search = `?c=${encoded}`;
  return url.toString();
}

function updateAddressBar() {
  if (!bridge || !state) return;
  try {
    window.history.replaceState(null, "", shareUrl());
  } catch (e) {
    // A bookmarkable link is a nicety, not a requirement; a failure here
    // should not interrupt editing.
    console.warn("could not update the address bar", e);
  }
}

// --- Selecting a starting point.

function selectStartingPoint(id) {
  const stateJson = bridge.stateForStart(id);
  state = JSON.parse(stateJson);
  gallerySection.hidden = true;
  editorSection.hidden = false;
  buildColorControls();
  buildHairControls();
  buildFaceControls();
  buildGarmentControls();
  renderPreview();
  updateAddressBar();
}

backButton.addEventListener("click", () => {
  editorSection.hidden = true;
  gallerySection.hidden = false;
  const url = new URL(window.location.href);
  url.search = "";
  window.history.replaceState(null, "", url);
});

// --- Downloads.

function slug() {
  // Not the character's name: a custom character built from a base has none,
  // and one built from a preset may no longer resemble it after edits, so
  // naming the file after the preset id would be a claim the file cannot back
  // up. "character" plus the download's own timestamp is honest instead.
  return `character-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}`;
}

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

downloadSvgBtn.addEventListener("click", () => {
  if (!bridge || !state) return;
  const svg = bridge.render(JSON.stringify(state), null, true);
  download(new Blob([svg], { type: "image/svg+xml" }), `${slug()}.svg`);
});

downloadPngBtn.addEventListener("click", async () => {
  if (!bridge || !state) return;
  const svg = bridge.render(JSON.stringify(state), null, true);
  const pngBytes = await svgToPngWithAttribution(svg, shareUrl());
  download(new Blob([pngBytes], { type: "image/png" }), `${slug()}.png`);
});

copyLinkBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shareUrl());
    copyLinkStatus.textContent = "Copied.";
  } catch (e) {
    copyLinkStatus.textContent = "Could not copy; the link is in the address bar.";
  }
  setTimeout(() => {
    copyLinkStatus.textContent = "";
  }, 3000);
});

// --- SVG to PNG in the browser, no cairo: docs/web-gui-plan.md's "PNG
// export, if wanted, happens in the browser". character.py emits no <text>,
// so an <img>-rendered SVG is safe. A tEXt chunk carries the same
// attribution the SVG's <metadata> block does, since a PNG a visitor saves
// and posts is the file least likely to keep the SVG's own metadata around.

async function svgToPngWithAttribution(svgText, characterLink) {
  const svgBlob = new Blob([svgText], { type: "image/svg+xml" });
  const svgUrl = URL.createObjectURL(svgBlob);
  try {
    const img = await loadImage(svgUrl);
    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    const bytes = new Uint8Array(await blob.arrayBuffer());
    return injectPngText(bytes, "Source", characterLink);
  } finally {
    URL.revokeObjectURL(svgUrl);
  }
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

// Splices a tEXt chunk (PNG spec, section 11.3.4.3) right after IHDR, the
// first chunk in every PNG `canvas.toBlob` writes. CRC32 covers the chunk
// type and data, per spec; the length and CRC are big-endian uint32s.
function injectPngText(bytes, keyword, text) {
  const PNG_SIGNATURE_LEN = 8;
  const ihdrLen = readUint32(bytes, PNG_SIGNATURE_LEN);
  const ihdrChunkLen = 4 + 4 + ihdrLen + 4; // length + type + data + crc
  const insertAt = PNG_SIGNATURE_LEN + ihdrChunkLen;

  const encoder = new TextEncoder();
  const data = new Uint8Array([...encoder.encode(keyword), 0, ...encoder.encode(text)]);
  const type = encoder.encode("tEXt");
  const crc = crc32(new Uint8Array([...type, ...data]));

  const chunk = new Uint8Array(4 + 4 + data.length + 4);
  writeUint32(chunk, 0, data.length);
  chunk.set(type, 4);
  chunk.set(data, 8);
  writeUint32(chunk, 8 + data.length, crc);

  const out = new Uint8Array(bytes.length + chunk.length);
  out.set(bytes.subarray(0, insertAt), 0);
  out.set(chunk, insertAt);
  out.set(bytes.subarray(insertAt), insertAt + chunk.length);
  return out;
}

function readUint32(bytes, offset) {
  return (bytes[offset] << 24) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3];
}

function writeUint32(bytes, offset, value) {
  bytes[offset] = (value >>> 24) & 0xff;
  bytes[offset + 1] = (value >>> 16) & 0xff;
  bytes[offset + 2] = (value >>> 8) & 0xff;
  bytes[offset + 3] = value & 0xff;
}

let CRC_TABLE = null;
function crc32(bytes) {
  if (!CRC_TABLE) {
    CRC_TABLE = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      CRC_TABLE[n] = c >>> 0;
    }
  }
  let crc = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) {
    crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// --- Startup.

async function main() {
  const catalogueResp = await fetch("ref-out/catalogue.json");
  if (!catalogueResp.ok) {
    setStatus("Could not load the character catalogue. Try reloading the page.", true);
    return;
  }
  catalogue = await catalogueResp.json();
  buildGallery();
  setStatus("Loading the in-browser Python runtime (a few megabytes, once)…");

  let pyodide;
  try {
    pyodide = await loadPyodide();
  } catch (e) {
    console.error(e);
    setStatus(
      "Could not load the Python runtime, so nothing here can be customised. " +
        "This can happen on a restrictive network. The gallery above still works: " +
        "every character can still be viewed and downloaded as-is.",
      true,
    );
    return;
  }

  pyodide.FS.mkdirTree("/pkg/anime_character_creator");
  for (const name of PACKAGE_FILES) {
    const resp = await fetch(`src/anime_character_creator/${name}`);
    const text = await resp.text();
    pyodide.FS.writeFile(`/pkg/anime_character_creator/${name}`, text);
  }
  pyodide.runPython('import sys\nsys.path.insert(0, "/pkg")');
  pyodide.runPython("from anime_character_creator import PRESETS");
  pyodide.runPython(BRIDGE_PY);

  bridge = {
    render: pyodide.globals.get("_bridge_render"),
    encode: pyodide.globals.get("_bridge_encode"),
    decode: pyodide.globals.get("_bridge_decode"),
    stateForStart: pyodide.globals.get("_bridge_state_for_start"),
  };

  enableGalleryCards();
  setStatus("");

  const params = new URLSearchParams(window.location.search);
  const shared = params.get("c");
  if (shared) {
    try {
      const stateJson = bridge.decode(shared);
      state = JSON.parse(stateJson);
      gallerySection.hidden = true;
      editorSection.hidden = false;
      buildColorControls();
      buildHairControls();
      buildFaceControls();
      buildGarmentControls();
      renderPreview();
    } catch (e) {
      console.warn("the link in the address bar did not decode", e);
      setStatus("That link did not look like one of ours; showing the gallery instead.");
    }
  }
}

main();
