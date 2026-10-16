// Python's `re.sub` replacement templates, which JavaScript does not have. Python reads `\1`, `\g<name>`, `\n`,
// `\\` and octal escapes in the replacement text, and `$` is an ordinary character; JS reads `$1`, `$&` and
// friends and `\` is ordinary. The drawing code builds a template out of a user-supplied `id_prefix`, so the
// difference is visible in the output for a prefix such as `a$&b` or `x\1`.
//
// The rules follow `re._parser.parse_template` of CPython 3.13. Error classes match the reference
// (CPython 3.13); the position text of the message is not reproduced (see the ledger).

import { PyError } from "./pynum.ts";

type Piece = string | number;

const ESCAPES: Record<string, string> = {
  a: "\x07",
  b: "\b",
  f: "\f",
  n: "\n",
  r: "\r",
  t: "\t",
  v: "\v",
  "\\": "\\",
};

// `re.error` is named `PatternError` from CPython 3.13 (and `error` before); the reference is 3.13.
const reError = (msg: string): PyError => new PyError("PatternError", msg);

/** Parse a replacement template for a pattern with `groups` capture groups into literals and group numbers. */
export function parseTemplate(source: string, groups: number): Piece[] {
  const out: Piece[] = [];
  let lit = "";
  const flush = (): void => {
    out.push(lit);
    lit = "";
  };
  const isDigit = (c: string | undefined): boolean => c !== undefined && c >= "0" && c <= "9";
  const isOct = (c: string | undefined): boolean => c !== undefined && c >= "0" && c <= "7";
  let i = 0;
  while (i < source.length) {
    const ch = source[i] as string;
    i++;
    if (ch !== "\\") {
      lit += ch;
      continue;
    }
    if (i >= source.length) throw reError("bad escape (end of pattern)");
    const c = source[i] as string;
    i++;
    if (c === "g") {
      if (source[i] !== "<") throw reError("missing <");
      i++;
      const end = source.indexOf(">", i);
      if (end < 0) throw reError("missing >, unterminated name");
      const name = source.slice(i, end);
      i = end + 1;
      if (name === "") throw reError("missing group name");
      if (/^[\p{L}_][\p{L}\p{N}_]*$/u.test(name)) throw new PyError("IndexError", `unknown group name '${name}'`);
      if (!/^[0-9]+$/.test(name)) throw reError(`bad character in group name '${name}'`);
      const index = Number(name);
      if (index > groups) throw reError(`invalid group reference ${index}`);
      flush();
      out.push(index);
    } else if (c === "0") {
      let digits = "0";
      if (isOct(source[i])) {
        digits += source[i++];
        if (isOct(source[i])) digits += source[i++];
      }
      lit += String.fromCharCode(parseInt(digits, 8) & 0xff);
    } else if (isDigit(c)) {
      let digits = c;
      let octal = false;
      if (isDigit(source[i])) {
        digits += source[i++];
        if (isOct(c) && isOct(digits[1]) && isOct(source[i])) {
          digits += source[i++];
          octal = true;
          const v = parseInt(digits, 8);
          if (v > 0o377) throw reError(`octal escape value \\${digits} outside of range 0-0o377`);
          lit += String.fromCharCode(v);
        }
      }
      if (!octal) {
        const index = Number(digits);
        if (index > groups) throw reError(`invalid group reference ${index}`);
        flush();
        out.push(index);
      }
    } else if (c in ESCAPES) {
      lit += ESCAPES[c];
    } else if (/[A-Za-z]/.test(c)) {
      throw reError(`bad escape \\${c}`);
    } else {
      lit += `\\${c}`;
    }
  }
  flush();
  return out;
}

/** `re.sub(pattern, template, text)` for a global regex with a Python-style template. The template is parsed
 * even when nothing matches, as Python does, so a bad escape raises regardless. */
export function pySub(pattern: RegExp, template: string, text: string): string {
  const nGroups = new RegExp(`${pattern.source}|`, pattern.flags).exec("")!.length - 1;
  const pieces = parseTemplate(template, nGroups);
  return text.replace(pattern, (...args: unknown[]) => {
    const groups = args.slice(0, 1 + nGroups) as (string | undefined)[];
    return pieces.map((p) => (typeof p === "string" ? p : (groups[p] ?? ""))).join("");
  });
}
