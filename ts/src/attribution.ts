// The `<metadata>` block `render_character(metadata=True)` can embed.
//
// `docs/web-gui-plan.md`'s licensing section settles what this says and why it
// has to be metadata rather than an enforced term: the permissive licence
// covers the code, forkable on purpose, which is what makes an attribution
// *clause* on the output unenforceable. What a claim of hand-drawing it *is*
// vulnerable to is the file itself saying otherwise, which is what this writes.
//
// Off by default on `render_character`, `render_sheet` and `render_cover`
// themselves, so the files `ref-out/` compares byte for byte do not churn on
// every unrelated change (a wording edit to `LICENSE_STATEMENT` or `TOOL_URL`
// below would otherwise touch every one of them at once). The CLI wrappers
// (`generate.py`, `sheet.py`, `cover.py`) default their own `--metadata` flag
// to *on*, since a file that leaves this repo is exactly the case this
// exists for; `refresh-ref-out.sh` passes `--no-metadata` explicitly to keep
// its own comparison clean. The web tool always turns it on for what a
// visitor downloads, the same way.
//
// Port notes. Only the block itself is here: `sheet_metadata_block` belongs with the sheet, and the PNG text
// chunk functions (`inject_png_text` and the two that call it) are not part of the port (zlib, struct).
// `render_character` embeds the block as `"  " + metadata_block(p) + "\n"` right after the `<svg>` line, which
// `character.ts`'s `documentWrap` already writes from the block it is given.

import type { CharacterParams } from "./params.ts";
import { pyReplace } from "./pynum.ts";
import { characterUrl } from "./urlstate.ts";

export const TOOL_URL = "https://rhedak.github.io/anime-character-creator/";
export const REPOSITORY_URL = "https://github.com/rhedak/anime-character-creator";
export const LICENSE_STATEMENT =
  "MIT License. Free to use, including commercially. " +
  "Please link back to the tool or the code, and please do not present this " +
  "as hand-drawn: a program drew it.";
export const NOVEL_TITLE = "The Hero of the Mist Tragedy";
export const NOVEL_URL = "https://www.honeyfeed.fm/novels/32712";

/**
 * `xml.sax.saxutils.escape(data, entities)`: `&`, `>` and `<` first, in that order, then each of `entities`
 * (a mapping from the text to replace to its replacement) in the order given.
 */
export function escape(data: string, entities: Readonly<Record<string, string>> = {}): string {
  let out = pyReplace(data, "&", "&amp;");
  out = pyReplace(out, ">", "&gt;");
  out = pyReplace(out, "<", "&lt;");
  for (const [k, v] of Object.entries(entities)) out = pyReplace(out, k, v);
  return out;
}

/**
 * The four lines every `<metadata>` block here carries regardless of
 * what it is attached to: the tool, the licence and the novel. Shared so
 * `metadata_block` and `sheet_metadata_block` cannot say two different
 * things about the same three facts.
 */
export function metadataHeader(): string {
  const titleAttr = escape(NOVEL_TITLE, { '"': "&quot;" });
  return (
    `    <source>${escape(TOOL_URL)}</source>\n` +
    `    <repository>${escape(REPOSITORY_URL)}</repository>\n` +
    `    <license>${escape(LICENSE_STATEMENT)}</license>\n` +
    `    <novel title="${titleAttr}">${escape(NOVEL_URL)}</novel>\n`
  );
}

/**
 * An SVG `<metadata>` element: the tool, the licence, the novel, and a
 * link that reproduces `p` exactly, all in one place so a downloaded file
 * carries its own provenance rather than depending on a page around it.
 */
export function metadataBlock(p: CharacterParams): string {
  const character = escape(characterUrl(p, TOOL_URL));
  return `<metadata>\n${metadataHeader()}    <character>${character}</character>\n  </metadata>`;
}
