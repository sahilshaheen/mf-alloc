from . import absl, dsp, icici, motilal, nippon, ppfas, sbi, uti, wealth

ADAPTERS = {m.AMC: m for m in (motilal, nippon, uti, wealth, sbi, icici, absl, dsp, ppfas)}
