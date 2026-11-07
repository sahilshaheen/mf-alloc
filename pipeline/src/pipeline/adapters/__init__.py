from . import motilal, nippon, uti, wealth

ADAPTERS = {m.AMC: m for m in (motilal, nippon, uti, wealth)}
