// A small XML reader for the rule tests. Node has no XML parser, and Python's `ElementTree.fromstring` was used in two ways:
// to prove a document is well-formed, and to read a little structure (the root's children, a metadata element's text,
// every element's text). This file does both. It is strict about what the renderer can get wrong (tag nesting, quoting,
// duplicate attributes, stray `<` or `&`, text outside the root) and ignores what it never emits (DTDs, namespaces
// beyond the plain `xmlns` attribute).
//
// A tag keeps the name it was written with. There are no namespace prefixes in the drawings, so ElementTree's
// `{http://www.w3.org/2000/svg}metadata` is just `metadata` here.

export interface XmlNode {
  readonly tag: string;
  readonly attrs: Readonly<Record<string, string>>;
  /** Text and child elements in document order. */
  readonly parts: (string | XmlNode)[];
}

/** The child elements of a node, in order (`list(el)`). */
export const childrenOf = (n: XmlNode): XmlNode[] => n.parts.filter((x): x is XmlNode => typeof x !== "string");

/** The first child element with this tag, or `undefined` (`el.find(tag)`). */
export const findChild = (n: XmlNode, tag: string): XmlNode | undefined => childrenOf(n).find((c) => c.tag === tag);

/** Every element in document order, the node itself first (`el.iter()`). */
export function* iterNodes(n: XmlNode): Generator<XmlNode> {
  yield n;
  for (const c of childrenOf(n)) yield* iterNodes(c);
}

/** All the text inside a node, in document order (`"".join(el.itertext())`). */
export function itertext(n: XmlNode): string {
  return n.parts.map((x) => (typeof x === "string" ? x : itertext(x))).join("");
}

const NAME = "[A-Za-z_][A-Za-z0-9_.:-]*";
const ATTR = new RegExp(`\\s+(${NAME})\\s*=\\s*("([^"<]*)"|'([^'<]*)')`, "y");
const OPEN = new RegExp(`<(${NAME})`, "y");
const CLOSE = new RegExp(`</(${NAME})\\s*>`, "y");

function decode(raw: string, what: string): string {
  return raw.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|[A-Za-z]+);/g, (_m, ent: string) => {
    if (ent === "amp") return "&";
    if (ent === "lt") return "<";
    if (ent === "gt") return ">";
    if (ent === "quot") return '"';
    if (ent === "apos") return "'";
    if (ent.startsWith("#x")) return String.fromCodePoint(parseInt(ent.slice(2), 16));
    if (ent.startsWith("#")) return String.fromCodePoint(parseInt(ent.slice(1), 10));
    throw new Error(`not well-formed: unknown entity &${ent}; in ${what}`);
  });
}

/** Reject a `&` that does not start a complete entity, and a `<` (which cannot be in text or an attribute value). */
function checkText(raw: string, what: string): void {
  const stripped = raw.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|[A-Za-z]+);/g, "");
  if (stripped.includes("&")) throw new Error(`not well-formed: bare & in ${what}`);
  if (stripped.includes("<")) throw new Error(`not well-formed: bare < in ${what}`);
}

/**
 * Parse one document and return its root element. Throws `Error("not well-formed: ...")` for anything
 * `ElementTree.fromstring` would refuse in the shapes the renderer can produce.
 */
export function parseXml(svg: string): XmlNode {
  let i = 0;
  const stack: XmlNode[] = [];
  let root: XmlNode | null = null;
  const fail = (why: string): never => {
    throw new Error(`not well-formed: ${why} at offset ${i}: ${JSON.stringify(svg.slice(i, i + 60))}`);
  };
  const addText = (raw: string): void => {
    if (raw === "") return;
    const top = stack[stack.length - 1];
    if (top === undefined) {
      if (raw.trim() !== "") fail("text outside the root element");
      return;
    }
    checkText(raw, "text");
    top.parts.push(decode(raw, "text"));
  };

  while (i < svg.length) {
    const lt = svg.indexOf("<", i);
    if (lt === -1) {
      addText(svg.slice(i));
      i = svg.length;
      break;
    }
    addText(svg.slice(i, lt));
    i = lt;
    if (svg.startsWith("<?", i)) {
      const end = svg.indexOf("?>", i);
      if (end === -1) fail("unterminated processing instruction");
      i = end + 2;
    } else if (svg.startsWith("<!--", i)) {
      const end = svg.indexOf("-->", i);
      if (end === -1) fail("unterminated comment");
      i = end + 3;
    } else if (svg.startsWith("<![CDATA[", i)) {
      const end = svg.indexOf("]]>", i);
      if (end === -1 || stack.length === 0) fail("bad CDATA section");
      stack[stack.length - 1]!.parts.push(svg.slice(i + 9, end));
      i = end + 3;
    } else if (svg.startsWith("</", i)) {
      CLOSE.lastIndex = i;
      const m = CLOSE.exec(svg);
      if (m === null) fail("bad closing tag");
      const open = stack.pop();
      if (open === undefined || open.tag !== m![1]) fail(`closing tag ${m![1]} does not match ${open?.tag ?? "nothing"}`);
      i = CLOSE.lastIndex;
    } else {
      OPEN.lastIndex = i;
      const m = OPEN.exec(svg);
      if (m === null) fail("bad opening tag");
      i = OPEN.lastIndex;
      const attrs: Record<string, string> = {};
      for (;;) {
        ATTR.lastIndex = i;
        const a = ATTR.exec(svg);
        if (a === null) break;
        const name = a[1]!;
        if (name in attrs) fail(`duplicate attribute ${name}`);
        const raw = a[3] ?? a[4] ?? "";
        checkText(raw, `attribute ${name}`);
        attrs[name] = decode(raw, `attribute ${name}`);
        i = ATTR.lastIndex;
      }
      const rest = /^\s*(\/?)>/.exec(svg.slice(i, i + 40));
      if (rest === null) fail("tag is not closed properly");
      const node: XmlNode = { tag: m![1]!, attrs, parts: [] };
      const top = stack[stack.length - 1];
      if (top !== undefined) top.parts.push(node);
      else if (root !== null) fail("a second root element");
      else root = node;
      i += rest![0].length;
      if (rest![1] === "") stack.push(node);
    }
  }
  if (stack.length > 0) fail(`unclosed element ${stack[stack.length - 1]!.tag}`);
  if (root === null) fail("no root element");
  return root as unknown as XmlNode;
}

/** `ET.fromstring(svg)`: parse and return the root, or throw. */
export const fromstring = parseXml;
