from . import absl, amfi, dsp, icici, motilal, nippon, ppfas, sbi, uti, wealth

# Portfolio sources plus reference inputs; `fetch all` pulls everything.
AMCS = {m.AMC: m for m in (uti, motilal, nippon, wealth, sbi, icici, absl, dsp, ppfas, amfi)}
