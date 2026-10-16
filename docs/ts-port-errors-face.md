# Rows for docs/ts-port-errors.md from the parts-face port

| Raised by | Python (3.12 / 3.13) | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `_jaw_track` or `_face_track` called with `steps=0` (no caller does; the beard passes the defaults 12 and 10) | `ZeroDivisionError: division by zero` (`i / steps` is int over int) | `ZeroDivisionError: float division by zero` (`pyDiv`) | the kernel has one text for both; the class is the same |
| `_eye` with `iris_aspect` a string that is not 1.0 (a hand-made link) | `ValueError: Unknown format code 'f' for object of type 'str'` from `f"{f.iris_aspect:.3f}"` | the same class and text (`fmt3Field` in `face.ts`) | reproduced |
| `_eye` with `iris_aspect` a list or `None` | `TypeError: unsupported format string passed to list.__format__` (or `NoneType.__format__`) | `TypeError: unsupported operand type(s): 'list' is not a number` | class equal, text is the `BadValue` stand-in's; nothing shows it |
| any arithmetic or comparison on a wrong-typed number field (`beard_length`, the `FaceStyle` numbers) | `TypeError` with CPython's operand text (`can't multiply sequence by non-int of type 'float'`, `'>' not supported between instances of 'str' and 'float'`, ...) | `TypeError: unsupported operand type(s): '<type>' is not a number` | the `BadValue` stand-in has one text; the class equals Python's in all 4,552 wrong-typed inputs tried (see the report) |
