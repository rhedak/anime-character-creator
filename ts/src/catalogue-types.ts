// The shapes `catalogue.py` builds its tables from (`ColorField`, `RangeField`, `BoolField`, `SelectField`,
// `GarmentSlot`, `StartingPoint`) and the helpers that check a field name against the real dataclasses
// (`_existing_fields`, `_color`, `_range`, `_bool`, `_face_range`, `_face_bool`, `_face_select`).
//
// Python's `dataclasses.fields()` is the field registry here (`FIELDS` in `model.ts`), the one thing TypeScript
// cannot reflect. A dataclass is a plain readonly object with the same attribute names. The generated tables
// (`catalogue-tables.ts`) call these constructors the way `catalogue.py` calls its own.

import { FIELDS } from "./model.ts";
import type { ClassName } from "./model.ts";
import { PyError, pyStrRepr } from "./pynum.ts";

export interface ColorField {
  readonly field: string;
  readonly label: string;
  // None if this color is always present (the tunic, the boots); a garment
  // with an optional color is off entirely when its value is None, which is
  // how `Outfit` already encodes "not worn" and why the web layer never
  // needs a separate presence flag.
  readonly optional: boolean;
}

export interface RangeField {
  readonly field: string;
  readonly label: string;
  readonly lo: number;
  readonly hi: number;
  /**
   * True where Python's `lo` and `hi` are ints (`RangeField("shoulder_bars", "Bars", 1, 4)`), so the JSON writes
   * `1` and `4` and not `1.0` and `4.0`. Every other range holds floats, whole-valued ones included (`0.0`).
   * JavaScript cannot tell the two by value, so the table says it.
   */
  readonly int?: true;
}

export interface BoolField {
  readonly field: string;
  readonly label: string;
}

/** A select option's value: whatever the real field holds. A number is an int (`scar_side`, `wristband_side`). */
export type OptionValue = null | string | number;

export interface SelectField {
  readonly field: string;
  readonly label: string;
  // Value/label pairs, in display order. Value is whatever the real field
  // holds (an int, for `scar_side`), not a string re-encoding of it, so the
  // bridge never has to translate a selection back into the model's own
  // type.
  readonly options: readonly (readonly [OptionValue, string])[];
}

/**
 * One layer of `Outfit`: its color and whatever else travels with it.
 *
 * `ranges` and `bools` are the companion fields that only mean anything once
 * the slot's color is set, `sleeve_drop` without a `robe_color` draws
 * nothing, so the web layer only needs to show them when the slot is on.
 */
export interface GarmentSlot {
  readonly id: string;
  readonly label: string;
  readonly color: ColorField;
  readonly ranges: readonly RangeField[];
  readonly bools: readonly BoolField[];
  // Named choices on `Outfit`, a traced cut being the first: `None` is the
  // shared parametric garment, offered first.
  readonly selects: readonly SelectField[];
  // A slot that only reads once another is already on: the pouches hang from
  // a belt, so offering them with no belt draws nothing and looks broken.
  readonly requires: string | null;
}

export interface StartingPoint {
  readonly id: string;
  readonly label: string;
}

// The dataclass constructors, with Python's defaults.

export const colorField = (field: string, label: string, optional = false): ColorField => ({ field, label, optional });

export const rangeField = (field: string, label: string, lo: number, hi: number, int?: true): RangeField =>
  int === undefined ? { field, label, lo, hi } : { field, label, lo, hi, int };

export const boolField = (field: string, label: string): BoolField => ({ field, label });

export const selectField = (field: string, label: string, options: readonly (readonly [OptionValue, string])[]): SelectField => ({
  field,
  label,
  options,
});

export interface GarmentSlotOptions {
  readonly ranges?: readonly RangeField[];
  readonly bools?: readonly BoolField[];
  readonly selects?: readonly SelectField[];
  readonly requires?: string | null;
}

export const garmentSlot = (id: string, label: string, color: ColorField, o: GarmentSlotOptions = {}): GarmentSlot => ({
  id,
  label,
  color,
  ranges: o.ranges ?? [],
  bools: o.bools ?? [],
  selects: o.selects ?? [],
  requires: o.requires ?? null,
});

// ---------------------------------------------------------------------------------------------------------
// Field names of the real dataclasses

/** `assert cond, message`: Python raises `AssertionError` with the message (empty when there is none). */
export function pyAssert(cond: boolean, message = ""): void {
  if (!cond) throw new PyError("AssertionError", message);
}

export function existingFields(cls: ClassName): ReadonlySet<string> {
  return new Set(FIELDS[cls].map((f) => f.name));
}

export const OUTFIT_FIELDS: ReadonlySet<string> = existingFields("Outfit");
export const CHARACTER_FIELDS: ReadonlySet<string> = existingFields("CharacterParams");
export const FACE_FIELDS: ReadonlySet<string> = existingFields("FaceStyle");

export function color(field: string, label: string, optional = true): ColorField {
  pyAssert(OUTFIT_FIELDS.has(field), `Outfit has no field ${pyStrRepr(field)}`);
  return colorField(field, label, optional);
}

export function range(field: string, label: string, lo: number, hi: number, int?: true): RangeField {
  pyAssert(OUTFIT_FIELDS.has(field), `Outfit has no field ${pyStrRepr(field)}`);
  return rangeField(field, label, lo, hi, int);
}

export function bool(field: string, label: string): BoolField {
  pyAssert(OUTFIT_FIELDS.has(field), `Outfit has no field ${pyStrRepr(field)}`);
  return boolField(field, label);
}

export function faceRange(field: string, label: string, lo: number, hi: number): RangeField {
  pyAssert(FACE_FIELDS.has(field), `FaceStyle has no field ${pyStrRepr(field)}`);
  return rangeField(field, label, lo, hi);
}

export function faceBool(field: string, label: string): BoolField {
  pyAssert(FACE_FIELDS.has(field), `FaceStyle has no field ${pyStrRepr(field)}`);
  return boolField(field, label);
}

export function faceSelect(field: string, label: string, options: readonly (readonly [OptionValue, string])[]): SelectField {
  pyAssert(FACE_FIELDS.has(field), `FaceStyle has no field ${pyStrRepr(field)}`);
  return selectField(field, label, options);
}

/** `set(labels) == set(table)`: the same keys, in any order. `table` is a registry (an object) or a tuple of names. */
export function assertKeysEqual(labels: object, table: object, message = ""): void {
  const a = new Set(Object.keys(labels));
  const b = new Set(Array.isArray(table) ? (table as readonly string[]) : Object.keys(table));
  pyAssert(a.size === b.size && [...a].every((k) => b.has(k)), message);
}

/** `table[key]` on a dict: `KeyError` with the key's repr when it is missing (a JS object would say `undefined`). */
export function lookup(table: Readonly<Record<string, string>>, key: string): string {
  if (!Object.hasOwn(table, key)) throw new PyError("KeyError", pyStrRepr(key));
  return table[key] as string;
}
