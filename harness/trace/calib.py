"""Check the calibration before trusting anything traced on it: our own head
outline, drawn in head-radius units, laid over the reference's face."""
import sys
sys.path.insert(0, "out/trace")
from trace import on_ref, on_ours, strip
sys.path.insert(0, "src")
from anime_character_creator import character as C

head = (C._head_shape(1.0), (0, 200, 255))
ear = (C._ear_outer(1.0), (255, 0, 200))
ear_l = (C._mirror(*C._ear_outer(1.0)), (255, 0, 200))
strip([on_ref([head, ear, ear_l], dash=0)], "out/trace/calib.png")
