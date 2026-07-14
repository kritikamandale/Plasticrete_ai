"""
Parametric materials science formulas for plastic concrete properties.
Used to generate physics_formula rows in the training dataset.
Calibrated against: Goh 2022, Colangelo 2018, Nayir 2024, Nafees 2022, Chong 2023.
"""
import numpy as np

PLASTIC_CS_FACTOR = {
    "PET":   0.92,
    "HDPE":  0.88,
    "LDPE":  0.82,
    "PVC":   0.85,
    "PP":    0.86,
    "Mixed": 0.87,
}

PLASTIC_TC_FACTOR = {
    "PET":   0.80,
    "HDPE":  0.72,
    "LDPE":  0.65,
    "PVC":   0.85,
    "PP":    0.70,
    "Mixed": 0.74,
}

ADDITIVE_CS_BOOST = {
    "fly_ash":     1.05,
    "silica_fume": 1.12,
    "fibres":      1.03,
    "none":        1.00,
}


def predict_properties(params: dict, noise_std: float = 0.05) -> dict:
    """
    Parametric prediction of all 7 M1 target properties.

    Calibration check (wc=0.45, pct=20, PET, no additive, 28d, 20C):
      CS_base = 55 * (0.35/0.45)^0.6 = 45.5
      CS_plas = 45.5 * 0.92 * (1 - 0.9*0.20) = 34.3 MPa
      Goh 2022 E2 = 37.5 MPa (within 10%)
    """
    ptype = params["plastic_type"]
    pct   = params["replacement_pct"]
    ps    = params["particle_size_mm"]
    wc    = params["wc_ratio"]
    atype = params["additive_type"]
    apct  = params["additive_pct"]
    temp  = params["curing_temp_c"]
    days  = params["curing_days"]

    seed = int(abs(wc * 1000 + pct * 100 + days)) % (2**31)
    rng  = np.random.default_rng(seed)

    # -- Compressive Strength (MPa) -----------------------------------------
    cs_base  = 55.0 * (0.35 / wc) ** 0.6
    plas_fac = PLASTIC_CS_FACTOR[ptype]
    plas_red = 1.0 - (0.90 * pct / 100.0)
    add_fac  = ADDITIVE_CS_BOOST[atype]
    add_scale= min(apct / 15.0, 1.0) if atype != "none" else 0.0
    add_eff  = 1.0 + (add_fac - 1.0) * add_scale
    cure_fac = 0.65 + 0.35 * (np.log(max(days, 1)) / np.log(90))
    temp_fac = 1.0 + 0.005 * (temp - 20.0)
    ps_fac   = 1.0 + 0.01 * (10.0 - min(ps, 20.0))

    cs = cs_base * plas_red * plas_fac * add_eff * cure_fac * temp_fac * ps_fac
    cs = max(cs + rng.normal(0, cs * noise_std), 2.0)

    # -- Flexural Strength (MPa) --------------------------------------------
    fs_ratio = 0.10 + 0.02 * (add_fac - 1.0)
    if atype == "fibres":
        fs_ratio = 0.14
    fs = cs * fs_ratio + rng.normal(0, 0.3)
    fs = max(fs, 0.5)

    # -- Split Tensile Strength (MPa) ---------------------------------------
    sts = cs * 0.095 + rng.normal(0, 0.2)
    sts = max(sts, 0.5)

    # -- Density (kg/m3) ----------------------------------------------------
    plastic_density = {"PET": 1380, "HDPE": 960, "LDPE": 920,
                       "PVC": 1400, "PP": 905, "Mixed": 1100}
    p_den   = plastic_density[ptype]
    density = 2400 * (1 - pct / 100) + p_den * (pct / 100)
    density += rng.normal(0, 30)
    density  = max(min(density, 2600), 900)

    # -- Water Absorption (%) -----------------------------------------------
    wa_base = 3.0 + 8.0 * (wc - 0.35) / 0.30
    wa_plas = wa_base * (1.0 - 0.3 * pct / 40.0)
    if atype in ["silica_fume", "fly_ash"]:
        wa_plas *= 0.75
    wa = wa_plas + rng.normal(0, 0.5)
    wa = max(min(wa, 25.0), 0.1)

    # -- Thermal Conductivity (W/mK) ----------------------------------------
    tc_concrete = 1.20
    tc_plastic  = {"PET": 0.29, "HDPE": 0.48, "LDPE": 0.33,
                   "PVC": 0.19, "PP":   0.22, "Mixed": 0.32}
    tc_p = tc_plastic[ptype]
    tc   = tc_concrete * (1 - pct / 100) + tc_p * (pct / 100)
    tc  *= PLASTIC_TC_FACTOR[ptype] ** (pct / 40.0)
    tc  += rng.normal(0, 0.05)
    tc   = max(min(tc, 2.5), 0.1)

    # -- Durability Index (0-100) -------------------------------------------
    dur = (
        40 * min(cs / 50.0, 1.0) +
        30 * max(0, (10 - wa) / 10) +
        20 * min(days / 28, 1.0) +
        10 * add_scale
    )
    dur += rng.normal(0, 3)
    dur  = max(min(dur, 100), 0)

    return {
        "compressive_strength_mpa": round(float(cs),  3),
        "flexural_strength_mpa":    round(float(fs),  3),
        "split_tensile_mpa":        round(float(sts), 3),
        "density_kgm3":             round(float(density), 1),
        "water_absorption_pct":     round(float(wa),  3),
        "thermal_conductivity_wm":  round(float(tc),  4),
        "durability_index":         round(float(dur), 2),
    }
