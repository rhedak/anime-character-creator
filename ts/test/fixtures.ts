// Decoding of the Python-side fixtures: "f:" + 16 hex digits of a big-endian IEEE-754 double, "i:" + decimal,
// "b:0|1", "s:" + text. See `harness/ts_port/synthetic.py` and `record.py`.

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
export const TS_ROOT = join(here, "..");
export const REPO_ROOT = join(TS_ROOT, "..");

const dv = new DataView(new ArrayBuffer(8));

export function decodeFloat(v: string): number {
  if (!v.startsWith("f:")) throw new Error(`not a float fixture value: ${v}`);
  const hex = v.slice(2);
  dv.setUint32(0, parseInt(hex.slice(0, 8), 16));
  dv.setUint32(4, parseInt(hex.slice(8, 16), 16));
  return dv.getFloat64(0);
}

export function encodeFloat(x: number): string {
  dv.setFloat64(0, x);
  return `f:${dv.getUint32(0).toString(16).padStart(8, "0")}${dv.getUint32(4).toString(16).padStart(8, "0")}`;
}

/** Same bits, so that nan equals nan and -0 differs from 0. */
export function sameBits(a: number, b: number): boolean {
  return encodeFloat(a) === encodeFloat(b) || (a !== a && b !== b);
}

export type Err = { err: string; msg?: string };
export const isErr = (v: unknown): v is Err => typeof v === "object" && v !== null && !Array.isArray(v) && "err" in v;

export function loadJson<T = any>(path: string): T {
  return JSON.parse(readFileSync(path, "utf8")) as T;
}

export const exists = (path: string): boolean => existsSync(path);
