class Mapping:

    CD = {
        "surrounded_high": 0.25,
        "surrounded_same": 0.5,
        "isolated": 1,
        "hilltop": 2
    }

    CI = {
        "aerial": 1,
        "buried": 0.3,
        "buried_mesh": 0.01
    }

    CT = {
        "lv_telecom_data_hv_with_transformer": 1,
        "hv_transformer_separated": 0.2
    }

    CE = {
        "rural": 1,
        "suburban": 0.5,
        "urban": 0.1,
        "urban_dense": 0.01
    }


    #B.1
    Pam = {

        "none": 1,

        "warning_notice": 1e-1,

        "electrical_insulation": 1e-2,

        "soil_equipotentialization": 1e-2,

        "natural_lps": 1e-3,
        # Natural LPS (NOTE 3, Annex B Table B.1)
        # Applicable when:
        # - Extensive metal framework
        # - Reinforced concrete with interconnected rods
        # - Meshed earth termination system
        # - No accessible metal installations connected to LPS

        "access_restriction": 0
    }

    

    rt = {

        "agricultural": 1e-2,
        "concrete": 1e-2,

        "marble": 1e-3,
        "ceramic": 1e-3,

        "gravel": 1e-4,
        "moquette": 1e-4,
        "carpet": 1e-4,

        "asphalt": 1e-5,
        "linoleum": 1e-5,
        "wood": 1e-5,

        "thick_insulation": 0
    }



    PLPS = {

        None: 1,

        "IV": 0.2,
        "III": 0.1,
        "II": 0.05,
        " I": 0.02,

        "I_natural": 0.01,

        "I_metal_roof": 0.001
    }



    PS = {
            "wood": 1,
            "masonry": 1,
            "reinforced_concrete": 0.5,
            "interconnected_metal_framework": 0.5
    }

   
    
    rP = {

        # rP = 0.5
        "extinguishers": 0.5,
        "hydrants": 0.5,
        "manual_alarm": 0.5,
        "fire_compartments": 0.5,
        "escape_route": 0.5,

        # rP = 0.2
        "automatic_alarm": 0.2,
        "automatic_extinguishing": 0.2
        
    }

    rF_fire = {
        "high": 1e-1,
        "ordinary": 1e-2,
        "low": 1e-3,
        "none": 0
    }

    rF_explosion = {
        "zone_0": 1,
        "zone_20": 1,
        "solid_explosive": 1,
        "zone_1": 1e-1,
        "zone_21": 1e-1,
        "zone_2": 1e-3,
        "zone_22": 1e-3
    }


    PSPD_POWER = {

        "S1": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01
        },

        "S2": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01
        },

        "S3": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01,
            "better_2_5": 1e-4,
            "better_3_75": 5e-5,
            "better_5": 1e-5
        },

        "S4": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01,
            "better_2_5": 1e-4,
            "better_3_75": 5e-5,
            "better_5": 1e-5
        }
    }

    PSPD_TELECOM = {

        "S1": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01
        },

        "S2": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01
        },

        "S3": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01,
            "better_2_5": 1e-4,
            "better_3_75": 5e-5,
            "better_5": 1e-5
        },

        "S4": {
            "none": 1,
            "III_IV": 0.05,
            "II": 0.02,
            "I": 0.01,
            "better_2_5": 1e-4,
            "better_3_75": 5e-5,
            "better_5": 1e-5
        }
    }


    KS3 = {

    # Table B.10

    "unshielded_no_routing_precaution": 1,  # ubah

    "unshielded_routing_precaution": 0.5,

    "unshielded_same_conduit": 0.2,

    "unshielded_same_cable": 0.01,

    "shielded_cable_bonded": 1e-4
    }

    PLD_LOW = {

    "unshielded": {

        0.35: 1,
        0.5: 1,
        1: 1,
        1.5: 1,
        2.5: 1,
        4: 1,
        6: 1,
        12: 1
    },

    "5_to_20": {

        0.35: 1,
        0.5: 1,
        1: 1,
        1.5: 1,
        2.5: 0.95,
        4: 0.9,
        6: 0.8,
        12: 0.4
    },

    "1_to_5": {

        0.35: 1,
        0.5: 1,
        1: 0.9,
        1.5: 0.8,
        2.5: 0.6,
        4: 0.3,
        6: 0.1,
        12: 0.02
    },

    "less_than_1": {

        0.35: 1,
        0.5: 0.85,
        1: 0.6,
        1.5: 0.4,
        2.5: 0.2,
        4: 0.04,
        6: 0.02,
        12: 0.005
    }
    }   
    
    PLD_HIGH = {

    "unshielded": {

        16: 1,
        20: 1,
        40: 1,
        60: 1,
        75: 1,
        95: 1
    },

    "5_to_20": {

        16: 0.3,
        20: 0.15,
        40: 0.03,
        60: 0.01,
        75: 0.007,
        95: 0.005
    },

    "1_to_5": {

        16: 0.01,
        20: 0.007,
        40: 0.0015,
        60: 0.001,
        75: 0.0004,
        95: 0.0002
    },

    "less_than_1": {

        16: 0.002,
        20: 0.0015,
        40: 0.0004,
        60: 0.00015,
        75: 0.0001,
        95: 0.00007
    }
    }

    PEB = {

    "none": 1,

    "III-IV": 0.05,

    "II": 0.02,

    "I": 0.01
    }

    LT = 1e-2

    LD_ALLOWED_VALUES = {
        "lower": 1e-2,
        "upper": 1e-1
    }


    LOSS_MAPPING = {

        "very_high": {
            "LF1": {
                "lower": 1e-2,
                "upper": 2e-1
            },
            "LF2": {
                "lower": 1e-2,
                "upper": 2e-1
            },
            "LO1": {
                "lower": 1e-3,
                "upper": 1e-2
            },
            "LO2": {
                "lower": 1e-3,
                "upper": 1e-2
            }
        },

        "high": {
            "LF1": {
                "lower": 1e-2,
                "upper": 1e-1
            },
            "LF2": {
                "lower": 1e-2,
                "upper": 1e-1
            },
            "LO1": {
                "lower": 1e-4,
                "upper": 1e-3
            },
            "LO2": {
                "lower": 1e-4,
                "upper": 1e-3
            }
        },

        "normal": {
            "LF1": {
                "lower": 5e-3,
                "upper": 5e-2
            },
            "LF2": {
                "lower": 5e-3,
                "upper": 5e-2
            },
            "LO1": {
                "lower": 1e-5,
                "upper_note_e": 5e-4
            },
            "LO2": {
                "lower": 1e-5,
                "upper_note_e": 5e-4
            }
        },

        "low": {
            "LF1": {
                "lower": 2e-3,
                "upper": 2e-2
            },
            "LF2": {
                "lower": 2e-3,
                "upper": 2e-2
            },
            "LO1": {
                "lower": 1e-5,
                "upper_note_e": 1e-4
            },
            "LO2": {
                "lower": 1e-5,
                "upper_note_e": 1e-4
            }
        }
    }

    ANNEX_E_PPE_MAPPING = {
    "working_site": 0.25,
    "working_site_more_than_one_shift": 1.0,
    "structures_open_to_public": 0.5,
    "zones_of_activities": 0.75,
    "residences": 1.0,
    "roads": 1.0,
    "railways": 0.25,
    "inland_waterways": 0.1,
    "pedestrian_ways": 0.75,
    "open_grounds_very_infrequent": 0.25,
    "infrequently_attended_areas": 0.25,
    "normally_or_frequently_attended": 0.5,
    "special_cases_sporadic": 0.1,
    "unknown": 1.0,
}

    ANNEX_E_L1_MAPPING = {
        "explosion_overpressure": {
            "inside_site_fence": {"LF1E": 0.25, "LO1E": 0.025},
            "outside_site_fence": {"LF1E": 0.5, "LO1E": 0.05},
        },
        "thermal_flux": {
            "inside_site_fence": {"LF1E": 0.05, "LO1E": 0.005},
            "outside_site_fence": {"LF1E": 0.1, "LO1E": 0.01},
        },
        "toxic_fumes": {
            "inside_site_fence": {"LF1E": 0.1, "LO1E": 0.01},
            "outside_site_fence": {"LF1E": 1.0, "LO1E": 0.1},
        },
        "soil_pollution": {
            "inside_site_fence": {"LF1E": 0.1, "LO1E": 0.01},
            "outside_site_fence": {"LF1E": 0.5, "LO1E": 0.05},
        },
        "water_pollution": {
            "inside_site_fence": {"LF1E": 0.25, "LO1E": 0.025},
            "outside_site_fence": {"LF1E": 2.5, "LO1E": 0.25},
        },
        "radioactive_material": {
            "inside_site_fence": {"LF1E": 0.5, "LO1E": 0.05},
            "outside_site_fence": {"LF1E": 5.0, "LO1E": 0.5},
        },
    } 

    ANNEX_E_L2_MAPPING = {
        "explosion_overpressure": {"LF2E": 0.5, "LO2E": 0.05},
        "thermal_flux": {"LF2E": 0.1, "LO2E": 0.01},
        "toxic_fumes": {"LF2E": 0.5, "LO2E": 0.05},
        "soil_pollution": {"LF2E": 0.2, "LO2E": 0.02},
        "water_pollution": {"LF2E": 0.5, "LO2E": 0.05},
        "radioactive_material": {"LF2E": 1.0, "LO2E": 0.1},
    }

    import math