# Franzi reference proportion analysis (script-only, no generation)
Scripts: common.py measure.py run_all.py step2.py step3.py step4.py. Data: measurements.json, measurements_normalised.csv, iou_results.json, seg_offsets.json.
Overlays: overlay-<A>-<B>.png (red=A, blue=B scaled by pupil-distance ratio and eye-centre aligned, white=overlap) for base-ref1/2/3/4, ref1-ref2, ref1-ref3, ref2-ref3, ref3-ref4, ref1-ref4, ref2-ref4.
Sheet: landmarks-normalised-ipd-sheet.png (all 5 scaled to equal pupil distance, eye line aligned, landmark lines); -small.png is a half-size copy.
Key: base/ref1-3 are 1312x1504 (NOT 893x1024), ref4 is 1008x1792. Head H = head top to chin (chin ~ +/-8px uncertain). ipd = pupil-to-pupil.
See final report in chat for the table and verdicts.
