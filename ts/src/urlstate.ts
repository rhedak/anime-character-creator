// A character, as a URL.
//
// `docs/web-gui-plan.md` takes this as a default worth having without being
// asked: "Encode the parameters into the address bar, so a made character is a
// link someone can send or bookmark." It also turns out to be what the
// metadata parameter on `render_character` needs, since "the parameter URL
// that reproduces the character" has to come from somewhere, so this lives
// next to `character.py` rather than under `web/`, and the JavaScript side of
// the web tool is a port of the same two functions rather than a second design.
//
// Full fidelity, not the catalogue's limited middle tier: a preset carries
// fields the web tool never exposes as a control (`scar_side`, `frame`, a
// disguise's `hair_tip_color=None`), and a shared link has to reproduce
// *that* character, not just the part of it a visitor could have built by
// hand. So this round-trips the whole of `CharacterParams`, encoding it as
// compact JSON, which stays legible in a browser's network tab and in a git
// diff, then URL-safe base64, which is what keeps it out of the characters a
// query string has to percent-encode.
//
// Port notes. The bytes are Python's: the JSON is `pyjson.dumps` with sorted keys and no whitespace, and which
// number is an int and which a float is read from the registry (`params.ts`), so `1.0` stays `1.0` and `3` stays
// `3`. A link is user input and Python keeps what it is given (`params_from_dict` checks field names, `finish`
// and `highlight_strength` and nothing else), so a field can hold an int where the registry says float, a string,
// a list; `pyvalue.ts` says how such a value is carried and written back. Reading is Python's too: the lenient
// base64 and `json.loads` of `pycodecs.ts` and `pyjsonload.ts`, with the same error text.

import { ADULT_FACE_AGE, FIELDS, characterParams, checkKeywords, faceStyle, outfit, replace, validateFinish } from "./model.ts";
import type { ClassName } from "./model.ts";
import { CHARACTERPARAMS_FIELDS, FACESTYLE_FIELDS, OUTFIT_FIELDS } from "./params.ts";
import type { CharacterParams, FaceStyle, FieldSpec, FieldType, Outfit } from "./params.ts";
import { PyInt, dumps } from "./pyjson.ts";
import type { Json } from "./pyjson.ts";
import { PyError } from "./pynum.ts";
import { asciiEncode, loadsBytes, urlsafeB64decode, urlsafeB64encode } from "./pycodecs.ts";
import { PyFloat, numberOf, pyTypeName, pyValueRepr } from "./pyvalue.ts";

// The query parameter a link carries the character under, short because it
// sits in a URL a person reads: `?c=...`.
export const QUERY_PARAM = "c";

// ---------------------------------------------------------------------------------------------------------
// The registry-typed view of a value

const isSafeInt = (n: number): boolean => Number.isSafeInteger(n);

/** A value of a field (or nested in one) as the JSON tree `dumps` writes, with the registry's tag deciding int or float. */
function jsonValue(tag: FieldType | undefined, v: unknown): Json {
  if (v === null || v === undefined) return null;
  if (typeof v === "boolean" || typeof v === "string") return v;
  if (v instanceof PyInt) return v;
  if (v instanceof PyFloat) return v.value;
  if (typeof v === "number") return tag === "int" && isSafeInt(v) ? new PyInt(v) : v;
  if (Array.isArray(v)) return v.map((x) => jsonValue(undefined, x));
  const entries = v instanceof Map ? [...v.entries()] : Object.entries(v as object);
  return new Map(entries.map(([k, x]) => [String(k), jsonValue(undefined, x)] as const));
}

function jsonObject(specs: readonly FieldSpec[], obj: object): Map<string, Json> {
  const record = obj as Readonly<Record<string, unknown>>;
  const out = new Map<string, Json>();
  for (const spec of specs) {
    const v = record[spec.name];
    if (v === undefined) throw new PyError("AttributeError", `object has no attribute '${spec.name}'`);
    if (spec.type === "Outfit") out.set(spec.name, jsonObject(OUTFIT_FIELDS, v as object));
    else if (spec.type === "FaceStyle") out.set(spec.name, jsonObject(FACESTYLE_FIELDS, v as object));
    else out.set(spec.name, jsonValue(spec.type, v));
  }
  return out;
}

/** Any of the four dataclasses as the JSON tree of its `asdict`, ready for `pyjson.dumps`. */
export function dataclassJson(cls: ClassName, obj: object): Json {
  return jsonObject(FIELDS[cls], obj);
}

/** `p` as the JSON tree of `asdict(p)`, ready for `pyjson.dumps`. */
export function paramsToJson(p: CharacterParams): Json {
  return jsonObject(CHARACTERPARAMS_FIELDS, p);
}

/** The compact, key-sorted JSON text `encode_params` encodes: `json.dumps(asdict(p), separators=(",", ":"), sort_keys=True)`. */
export function paramsJsonText(p: CharacterParams): string {
  return dumps(paramsToJson(p), { sortKeys: true, compact: true });
}

/**
 * `p` as a plain, JSON-able dict: `dataclasses.asdict`, named so the web
 * bridge has one obvious function to call rather than an
 * import of its own. Nested dataclasses become plain objects, copied; the values are carried as they are.
 */
export function paramsToDict(p: CharacterParams): Record<string, unknown> {
  const copy = (specs: readonly FieldSpec[], obj: object): Record<string, unknown> => {
    const record = obj as Readonly<Record<string, unknown>>;
    const out: Record<string, unknown> = {};
    for (const spec of specs) {
      const v = record[spec.name];
      if (spec.type === "Outfit") out[spec.name] = copy(OUTFIT_FIELDS, v as object);
      else if (spec.type === "FaceStyle") out[spec.name] = copy(FACESTYLE_FIELDS, v as object);
      else out[spec.name] = v;
    }
    return out;
  };
  return copy(CHARACTERPARAMS_FIELDS, p);
}

// ---------------------------------------------------------------------------------------------------------
// dict(x), Cls(**x)

/** `type(x).__name__` for a decoded value, for the messages Python builds from it. */
const typeName = (v: unknown): string => pyTypeName(v);

const asMap = (v: unknown): Map<unknown, unknown> | undefined => {
  if (v instanceof Map) return new Map(v);
  if (v !== null && typeof v === "object" && !Array.isArray(v) && !(v instanceof PyInt) && !(v instanceof PyFloat)) {
    return new Map(Object.entries(v));
  }
  return undefined;
};

/**
 * `dict(value)` for whatever a link put where a dict belongs: a dict is copied, a list of pairs (or of strings of
 * two characters) is read as pairs, and anything else raises what Python raises, with its text.
 */
export function pyDict(value: unknown): Map<unknown, unknown> {
  const m = asMap(value);
  if (m !== undefined) return m;
  const notIterable = (): PyError => new PyError("TypeError", `'${typeName(value)}' object is not iterable`);
  if (value === null || value === undefined || typeof value !== "object" && typeof value !== "string") throw notIterable();
  if (value instanceof PyInt || value instanceof PyFloat) throw notIterable();
  const elements: unknown[] = typeof value === "string" ? Array.from(value) : (value as unknown[]);
  const out = new Map<unknown, unknown>();
  elements.forEach((el, i) => {
    let pair: unknown[];
    if (Array.isArray(el)) pair = el;
    else if (typeof el === "string") pair = Array.from(el);
    else if (asMap(el) !== undefined) pair = [...(asMap(el) as Map<unknown, unknown>).keys()];
    else throw new PyError("TypeError", `cannot convert dictionary update sequence element #${i} to a sequence`);
    if (pair.length !== 2) {
      throw new PyError("ValueError", `dictionary update sequence element #${i} has length ${pair.length}; 2 is required`);
    }
    const key = pair[0];
    if (Array.isArray(key) || asMap(key) !== undefined) throw new PyError("TypeError", `unhashable type: '${typeName(key)}'`);
    // Equal keys are one key (`1`, `1.0` and `True` too), told apart here by their spelling in Python.
    const id = typeof key === "string" ? key : pyValueRepr(key);
    const found = typeof key === "string" ? undefined : [...out.keys()].find((k) => k instanceof NonStringKey && k.repr === id);
    out.set(typeof key === "string" ? key : (found ?? new NonStringKey(id)), pair[1]);
  });
  return out;
}

/** A dict key that is not a string (`dict([[1, 2]])`), which `Cls(**d)` then refuses. */
class NonStringKey {
  readonly repr: string;
  constructor(repr: string) {
    this.repr = repr;
  }
}

/** The keys of a dict that is about to be `**`-expanded: all of them must be strings. */
function keywords(m: ReadonlyMap<unknown, unknown>): [string, unknown][] {
  const out: [string, unknown][] = [];
  for (const [k, v] of m) {
    if (typeof k !== "string") throw new PyError("TypeError", "keywords must be strings");
    out.push([k, v]);
  }
  return out;
}

/** `Cls(**value)` needs a mapping. */
function mappingFor(cls: string, value: unknown): ReadonlyMap<unknown, unknown> {
  const m = asMap(value);
  if (m === undefined) {
    throw new PyError("TypeError", `anime_character_creator.character.${cls}() argument after ** must be a mapping, not ${typeName(value)}`);
  }
  return m;
}

/**
 * What a field of the registry holds, for a value read out of JSON text (`loads`: an int is a `PyInt`, a float a
 * plain number): the registry's own reading where it agrees, and a marker where the JSON said something else.
 */
function fromWire(tag: FieldType, v: unknown): unknown {
  if (tag === "int") {
    if (v instanceof PyInt) return isSafeInt(Number(v.value)) && typeof v.value === "number" ? v.value : v;
    if (typeof v === "number" && Number.isInteger(v)) return new PyFloat(v);
  }
  return v;
}

function fieldsFrom(cls: ClassName, specs: readonly FieldSpec[], m: ReadonlyMap<unknown, unknown>, wire: boolean): Record<string, unknown> {
  const pairs = keywords(m);
  checkKeywords(
    cls,
    pairs.map(([k]) => k),
  );
  const tags = new Map(specs.map((s) => [s.name, s.type] as const));
  return Object.fromEntries(pairs.map(([k, v]) => [k, wire ? fromWire(tags.get(k) as FieldType, v) : v]));
}

// ---------------------------------------------------------------------------------------------------------
// params_from_dict, encode, decode

/** `a < b` for a value and the adult floor: a number compares, anything else is Python's `TypeError`. */
function lessThanAdult(v: unknown): boolean {
  const n = numberOf(v);
  if (n === undefined) {
    throw new PyError("TypeError", `'<' not supported between instances of '${typeName(v)}' and 'float'`);
  }
  return n < ADULT_FACE_AGE;
}

/**
 * The inverse of `paramsToDict`, and the validating half both
 * `decodeParams` and the web bridge's live-edit path share: a dict in,
 * however it arrived, either becomes a real `CharacterParams` or raises
 * `ValueError`, never a character quietly missing the fields that failed.
 *
 * `data` is either what `loads` returned (a `Map`, where a `PyInt` is an int and a plain number a float, so a
 * whole-valued float in an int field and an int in a float field are kept as they came) or a plain object whose
 * numbers mean what the registry says.
 */
export function paramsFromDict(input: ReadonlyMap<string, unknown> | Readonly<Record<string, unknown>>): CharacterParams {
  const wire = input instanceof Map;
  const data = new Map<unknown, unknown>(input instanceof Map ? input : Object.entries(input));
  // The realistic build and the compressed chibi are retired
  // (`docs/tall-chibi-plan.md`): a link from before carrying another build or
  // `body: null` loads as the default tall chibi rather than failing.
  data.delete("heads");
  if (data.has("body") && data.get("body") === null) data.delete("body");
  // `long_traced_real` was that build's own haircut and went with it; its
  // chibi counterpart is the same cut.
  if (data.get("hairstyle") === "long_traced_real") {
    data.set("hairstyle", "long_traced");
  }
  // The second eye style (`anime`) went with its `eye_glow` knob
  // (`docs/detail-plan.md`); a link carrying either loads with the one eye.
  const popFace = data.has("face") ? data.get("face") : new Map();
  data.delete("face");
  const faceData = pyDict(popFace);
  faceData.delete("eye_style");
  faceData.delete("eye_glow");
  let p: CharacterParams;
  try {
    const popOutfit = data.has("outfit") ? data.get("outfit") : new Map();
    data.delete("outfit");
    const outfitValue: Outfit = outfit(fieldsFrom("Outfit", OUTFIT_FIELDS, mappingFor("Outfit", popOutfit), wire) as Partial<Outfit>);
    const faceValue: FaceStyle = faceStyle(fieldsFrom("FaceStyle", FACESTYLE_FIELDS, faceData, wire) as Partial<FaceStyle>);
    const top = fieldsFrom("CharacterParams", CHARACTERPARAMS_FIELDS, data, wire);
    p = characterParams({ ...top, outfit: outfitValue, face: faceValue } as Partial<CharacterParams>);
  } catch (e) {
    if (e instanceof PyError && e.pyType === "TypeError") {
      throw new PyError("ValueError", `not a valid character: ${e.message.slice("TypeError: ".length)}`);
    }
    throw e;
  }
  // This is where a character from outside arrives (a link, the web tool, a
  // companion app's model). Nothing that comes in this way is drawn younger
  // than the adult floor, whatever it asks for, and a link that did is raised
  // rather than refused.
  if (lessThanAdult(p.face_age)) {
    p = replace(p, { face_age: ADULT_FACE_AGE });
  }
  // A link can carry the soft finish's two fields although the web tool has no control for
  // them; a bad value is refused here rather than failing later inside the renderer.
  validateFinish(p);
  return p;
}

/**
 * `p`, as the value half of a `?c=...` query parameter.
 *
 * Deterministic: sorted keys and no whitespace, so the same character
 * always encodes to the same string, which is what lets two links be
 * compared for equality without decoding either.
 */
export function encodeParams(p: CharacterParams): string {
  const data = paramsJsonText(p);
  return urlsafeB64encode(asciiEncode(data)).replace(/=+$/, "");
}

/** Python's `str(e)` of an error that `decode_params` swallows into its own. */
const messageOf = (e: PyError): string => e.message.slice(e.pyType.length + 2);

/**
 * The inverse of `encodeParams`.
 *
 * Raises `ValueError` on anything that is not one of this project's own
 * links: malformed base64, JSON that is not an object, or a key that is
 * not a real field on `CharacterParams`, `Outfit` or `FaceStyle`. A link
 * typed in by hand or mangled by a chat client should fail loudly here
 * rather than build a character out of whatever survived.
 */
export function decodeParams(encoded: string): CharacterParams {
  const length = Array.from(encoded).length;
  const padded = encoded + "=".repeat((4 - (length % 4)) % 4);
  let data: Json;
  try {
    data = loadsBytes(urlsafeB64decode(asciiEncode(padded)));
  } catch (e) {
    if (e instanceof PyError) throw new PyError("ValueError", `not a valid character link: ${messageOf(e)}`);
    throw e;
  }
  if (!(data instanceof Map)) {
    throw new PyError("ValueError", "not a valid character link: not an object");
  }
  return paramsFromDict(data);
}

/**
 * The full link for `p`, off `base_url`, which is the deployed page's own
 * address and not something this module invents.
 */
export function characterUrl(p: CharacterParams, baseUrl: string): string {
  return `${baseUrl}?${QUERY_PARAM}=${encodeParams(p)}`;
}
