"""All numeric thresholds and weights for M3 scoring engine."""

BASELINE_CO2_KGM3 = 365.71  # conventional M20 concrete, Goh et al. 2022

PLASTIC_TYPES  = ["PET", "HDPE", "LDPE", "PVC", "PP", "Mixed"]
ADDITIVE_TYPES = ["fly_ash", "silica_fume", "fibres", "none"]

# IS 10262:2019 M20 reference mix
CEMENT_BASELINE_KGM3     = 383.0
FINE_AGG_BASELINE_KGM3   = 680.0
COARSE_AGG_BASELINE_KGM3 = 1210.0

# BIS thresholds
IS_1237_MIN_CS_MPA           = 30.0
IS_1237_MAX_WA_PCT           = 1.0
IS_2185_PT1_MIN_CS_MPA       = 3.5
IS_2185_PT2_MAX_DENSITY      = 1500.0
IS_2185_PT2_MAX_WA_PCT       = 10.0
IS_5816_MIN_STS_CS_RATIO     = 0.10
IS_5816_MIN_STS_MPA          = 1.5
NBC_STRUCTURAL_MIN_CS_MPA    = 20.0
NBC_STRUCTURAL_MIN_DENSITY   = 1800.0
NBC_STRUCTURAL_MAX_DENSITY   = 2500.0
NBC_NONSTRUCTURAL_MIN_CS_MPA = 5.0
NBC_NONSTRUCTURAL_MAX_DENSITY= 1800.0

# Sustainability score normalisation bounds
CARBON_SCORE_LOW  = -50.0   # % saving (worst case)
CARBON_SCORE_HIGH = 130.0   # normalisation range width
DIVERSION_MAX     = 200.0   # kg/m3
REPLACEMENT_MAX   = 40.0    # %
N_BIS_STANDARDS   = 7
N_GREEN_CREDITS   = 7
