// Generated once by harness/ts_port/gen_face_tables.py from the Python tables, then owned by hand.

import type { Point, Segment } from "./tables.ts";

/** The ear's rim, in the ear's own frame: where it leaves the top attach. */
export const EAR_ARC_START: Point = [0, 0];

/** The ear's rim: four quadratics, top attach to bottom attach. */
export const EAR_ARC: readonly Segment[] = [[[0.008, 0.345], [0.135, 0.655]], [[0.273, 0.943], [0.5, 1]], [[0.661, 0.944], [0.779, 0.768]], [[0.963, 0.406], [1, 0]]];

/** The antihelix's start, in the ear's own frame. */
export const EAR_FOLD_START: Point = [0.404, 1];

/** The antihelix, one question-mark stroke. */
export const EAR_FOLD: readonly Segment[] = [[[0.294, 0.955], [0.255, 0.778]], [[0.229, 0.591], [0.26, 0.408]], [[0.338, 0.255], [0.428, 0.105]], [[0.43, 0.402], [0.615, 0.465]], [[0.731, 0.258], [0.731, 0]]];
