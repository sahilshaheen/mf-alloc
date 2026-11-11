from . import (
    absl,
    axis,
    dsp,
    hdfc,
    icici,
    iti,
    kotak,
    mahindra,
    mirae,
    motilal,
    nippon,
    ppfas,
    sbi,
    tata,
    uti,
    wealth,
    whiteoak,
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
        kotak,
        mahindra,
        whiteoak,
        iti,
        axis,
    )
}
