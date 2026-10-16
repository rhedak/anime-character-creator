// The part registry: every function `render_character` calls, by its Python name, so the assembly (`render.ts`) can run with
// whatever is ported so far and say plainly what is missing. A domain module adds its parts by exporting a `PARTS` object;
// `render.ts` merges them. A part not yet ported is simply absent.

import type { CharacterParams } from "./params.ts";
import type { Skeleton } from "./skeleton.ts";

/** A part of the drawing: SVG text from the skeleton and the parameters, plus whatever extra arguments its slot passes. */
export type PartFn = (sk: Skeleton, p: CharacterParams, ...extra: any[]) => string;

/** A part that wraps another part's text (`_hair_lines(svg, p)`, `_without_raised_sleeves(svg, p)`). */
export type WrapFn = (svg: string, p: CharacterParams) => string;

export type PartTable = Readonly<Record<string, ((...args: any[]) => any) | undefined>>;
