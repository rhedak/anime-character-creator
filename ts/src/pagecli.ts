// What `bin/cover.ts` and `bin/sheet.ts` share: the parts of argparse and `pathlib` their Python counterparts lean on.
// Exit codes follow argparse: 2 for a bad argument (usage and a message on stderr), 0 on success.

import { extname } from "node:path";
import { PyError, pyFloat } from "./pynum.ts";

/** What a command line gave for one `--flag` / `--no-flag` pair: the last one on the line wins, as `BooleanOptionalAction` does. */
export function lastOf(tokens: readonly { kind: string; name?: string }[], on: string, off: string, fallback: boolean): boolean {
  let value = fallback;
  for (const t of tokens) {
    if (t.kind !== "option") continue;
    if (t.name === on) value = true;
    else if (t.name === off) value = false;
  }
  return value;
}

/** argparse's `type=float`, or `usage` with its message. */
export function floatArg(flag: string, text: string, fail: (message: string) => never): number {
  try {
    return pyFloat(text);
  } catch (e) {
    if (e instanceof PyError) return fail(`argument ${flag}: invalid float value: '${text}'`);
    throw e;
  }
}

/** argparse's `type=int`: `int(text)` accepts surrounding space, a sign and single underscores between digits. */
export function intArg(flag: string, text: string, fail: (message: string) => never): number {
  const t = text.trim();
  if (!/^[+-]?\d+(_\d+)*$/.test(t)) return fail(`argument ${flag}: invalid int value: '${text}'`);
  return Number(t.replaceAll("_", ""));
}

/** argparse's `choices=`. */
export function choiceArg(flag: string, value: string, choices: readonly string[], fail: (message: string) => never): string {
  if (!choices.includes(value)) return fail(`argument ${flag}: invalid choice: '${value}' (choose from ${choices.join(", ")})`);
  return value;
}

/** Python's `Path(out).with_suffix(suffix)` as text: an existing extension is replaced, not kept. */
export function withSuffix(out: string, suffix: string): string {
  return `${out.slice(0, out.length - extname(out).length)}${suffix}`;
}

/**
 * Run `main`, and report a Python exception as the Python CLI's traceback ends, `Class: message`, exit code 1, rather than as a
 * Node stack. Anything else is a bug and propagates.
 */
export function runMain(main: () => void): void {
  try {
    main();
  } catch (e) {
    if (!(e instanceof PyError)) throw e;
    process.stderr.write(`${e.message}\n`);
    process.exit(1);
  }
}
