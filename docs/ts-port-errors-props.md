# Error-text differences in the props port (rows for docs/ts-port-errors.md)

| Raised by | Python (3.12 / 3.13) | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `_katana` / `_katana_placement` / `_katana_stretch_factor` with a non-number `katana_length` (a string, list or `None` from a link) | `TypeError: unsupported operand type(s) for -: 'str' and 'float'` (the text names the operator and both types) | `TypeError` with the kernel's `BadValue` text (`unsupported operand type(s): 'str' is not a number`) | the class is Python's and is raised at the same first use (`length - 1.0`); the operator and the other operand's type are not tracked |
| `_staff`, `_headscarf`, `_familiar`, `_hat` with a non-number in a float field the part computes with (`right_arm_out`, `left_arm_out`) | `TypeError` naming the operator and types | `TypeError` with the kernel's `BadValue` text | as above |
| a non-string colour in a field the part prints without parsing (`hat_color`, `headscarf_color`, `staff_color`, `familiar_color`, ...) | the attribute holds `str(value)` (`fill="5"`, `fill="True"`, `fill="['#fff']"`) | the same text (`pyStr` in `props.ts`, `pyValueRepr` for the non-string) | none: reproduced exactly on the corpus (`err-colour-*` cases); where a colour is parsed first (`shade`) both sides raise |
