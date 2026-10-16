// The tag scanner the rule tests use instead of `ElementTree` (ts/test/svg-scan.ts). Not a port of a Python test: a control, so that
// every "well-formed" assertion in the rules means something. Checked offline against `ET.fromstring` on all 22 characters in
// both finishes: the same element count, the same text length and the same attribute count (plus the one `xmlns`, which
// ElementTree turns into a namespace).

import assert from "node:assert/strict";
import { test } from "node:test";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { childrenOf, findChild, fromstring, iterNodes, itertext } from "./svg-scan.ts";

test("the scanner reads structure, attributes and decoded text", () => {
  const root = fromstring('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><!-- c --><metadata><a>x &amp; y &lt;z&gt; &#65;</a><b/></metadata><rect width=\'100%\' fill="#fff" /></svg>');
  assert.equal(root.tag, "svg");
  assert.deepEqual(childrenOf(root).map((c) => c.tag), ["metadata", "rect"]);
  assert.equal(itertext(findChild(findChild(root, "metadata")!, "a")!), "x & y <z> A");
  assert.equal(childrenOf(root)[1]!.attrs.width, "100%");
  assert.deepEqual([...iterNodes(root)].map((n) => n.tag), ["svg", "metadata", "a", "b", "rect"]);
});

const MALFORMED: [string, string][] = [
  ["mismatched tags", "<svg><g></svg></g>"],
  ["unclosed element", "<svg><g></svg>"],
  ["bare ampersand in text", "<svg>a & b</svg>"],
  ["bare ampersand in an attribute", '<svg a="x & y"></svg>'],
  ["unknown entity", "<svg>&nbsp;</svg>"],
  ["duplicate attribute", '<svg a="1" a="2"></svg>'],
  ["unquoted attribute", "<svg a=1></svg>"],
  ["less-than in an attribute", '<svg a="<"></svg>'],
  ["two roots", "<svg></svg><svg></svg>"],
  ["text outside the root", "x<svg></svg>"],
  ["no root", "  "],
  ["unterminated tag", '<svg a="1"'],
];
for (const [label, doc] of MALFORMED) {
  test(`the scanner refuses a malformed document: ${label}`, () => {
    assert.throws(() => fromstring(doc), /not well-formed/);
  });
}

test("the scanner accepts what the renderer writes and sees a broken copy of it", () => {
  const svg = renderCharacter(PRESETS.satoko);
  const root = fromstring(svg);
  assert.equal(root.tag, "svg");
  assert.ok([...iterNodes(root)].length > 100);
  assert.throws(() => fromstring(svg.replace("</svg>", "")), /not well-formed/);
  assert.throws(() => fromstring(svg.replace('id="hair-tips"', 'id="hair-tips" id="again"')), /duplicate attribute/);
});
