from . import absl, icici, motilal, nippon, sbi, uti, wealth

ADAPTERS = {m.AMC: m for m in (motilal, nippon, uti, wealth, sbi, icici, absl)}
