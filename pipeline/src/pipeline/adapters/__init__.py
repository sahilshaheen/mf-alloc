from . import (
    absl,
    dsp,
    hdfc,
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

ADAPTERS = {
    m.AMC: m
    for m in (
        motilal,
        nippon,
        uti,
        wealth,
        sbi,
        icici,
        absl,
        dsp,
        ppfas,
        mirae,
        tata,
        hdfc,
    )
}
