// Prints the fields of the catalogue that change nothing in a body's drawing (docs/adult-body-audit.md, C), found by drawing Franzi on it.
//   node harness/franzi/ignored_fields.ts [BODY]        default adult_female
import { ignoredFields } from "../../ts/test/ignored-fields.ts";

const body = process.argv[2] ?? "adult_female";
console.log(JSON.stringify(ignoredFields(body)));
