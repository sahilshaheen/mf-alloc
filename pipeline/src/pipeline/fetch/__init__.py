from . import (
    absl,
    amfi,
    dsp,
    icici,
    mirae,
    motilal,
    nippon,
    ppfas,
    sbi,
    tata,
    uti,
    wealth,
)

# Portfolio sources plus reference inputs; `fetch all` pulls everything.
AMCS = {m.AMC: m for m in (uti, motilal, nippon, wealth, sbi, icici, absl, dsp, ppfas, mirae, tata, amfi)}
