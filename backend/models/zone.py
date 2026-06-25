class Zone:

    def __init__(self, name):

        self.name = name

        # People
        self.people_present = False   #PO
        self.people_exposed_on_structure = False

        # Internal system
        self.internal_system_present = False
        

        #self.Pe = 1.0

        # ------------------------------
        # rt — reduction factor (Table B.2)// floor type
        # ------------------------------
        self.floor_type = "linoleum" #rt
        
        # ------------------------------
        # Pam — protection measure (Table B.1)// protection against shock
        # ------------------------------
        self.touch_protection = [    #Pam(shochl protection)
          #  "warning_notice",
           # "electrical_ninsulatio"
        ]          

        # "warning_notice",
            # "electrical_insulation",
            # "soil_equipotentialization",
            # "access_restriction"
        
        # ------------------------------
        # rP — fire protection (Table B.5)
        # ------------------------------
        self.fire_protection = [
        # "extinguishers",
        # "hydrants",
           #"automatic_alarm"
        # "automatic_extinguishing"
        ]
        # ------------------------------
        # rP — special condition
        # ------------------------------
        
        # "none", "low", "ordinary", "high"
        self.explosion_zone = False
        self.lithium_battery_zone = False
        # ------------------------------
        # rf — fire risk (Table B.6)// risk of fire
        # ------------------------------
        self.fire_risk = "low"
        # "none", "low", "ordinary", "high"

        # ------------------------------
        # rf — explosion classification
        # ------------------------------
        self.explosion_zone_type = None
        # "zone_0", "zone_1", "zone_2"
        # "zone_20", "zone_21", "zone_22"
        # "solid_explosive"
        
        # ------------------------------
        # rf — NOte 7 conditions
        # ------------------------------
        self.explosive_presence_per_year = None
        self.negligible_extent = False
        self.direct_strike_protected = False
        self.metal_shelter = False
        self.lps_protected = False
        self.natural_lps_structure = False
        self.internal_system_protected = False
        
        # operational state (Annex sometimes considers this)
        #self.operational = True



        self.people_in_LPS_area = False  #check guna kt mna

        # ------------------------------
        # Pspd
        # ------------------------------
        # Power line SPD
        self.power_spd_level = "none"
        self.power_use_custom_pspd = False
        self.power_custom_pspd = None

        # Telecom line SPD
        self.telecom_spd_level = "none"
        self.telecom_use_custom_pspd = False
        self.telecom_custom_pspd = None
        
        # OPTIONS:
        # none
        # III_IV
        # II
        # I
        # better_2_5
        # better_3_75
        # better_5


        # ------------------------------
        # KS2 / internal shielding
        # ------------------------------

        # Internal shielding exists
        self.internal_shielding = False

        # Spatial shield width wm2 (m)
        self.wm2 = None

        # Continuous internal metal shield
        self.continuous_metal_shield = False
        self.meshed_bonding_network = False


          #------------------------------
        # KS3 / internal wiring
        # ------------------------------

        # Whether a metallic internal system exists for each service.
        # Office case: external telecom fibre but internal copper -> telecom True.
        # Hospital case: external + internal both fibre -> telecom False.
        self.has_power_internal_system = True

        self.has_telecom_internal_system = True

        self.power_internal_wiring = (
        #"unshielded_same_conduit"
        )

        self.telecom_internal_wiring = (
           # "unshielded_no_routing_precaution"
        )

        # Presence time per year (hours)
        self.tz = None
        # Equipment exposure time per year (hours)
        self.te = None

        # ==================================================
        # ANNEX C — LOSS CLASSIFICATION
        # ==================================================

        #for category
        # "very_high"-explosion risk zone, ex: ICU, explosive chemical storage, strucutre danegrous to enviroment
        # "high"-high loss, ex: hospital room (people less mobility), prison, industrial control rooms, attraction building
        # "normal"-normal public access structure/zone, ex: school, offices, hotels etc
        # "low"-building in private ownership ex: residential, farm house
        

        self.loss_category = "normal"
   #     self.loss_value_level = "upper"

        #value_level- "lower" "upper"
        self.LT_applicable = True

# LD
        self.LD_applicable = False
        self.LD_value_level = None

# LF1
        self.LF1_applicable = False
        self.LF1_value_level = None

# LF2
        self.LF2_applicable = False
        self.LF2_value_level = None
# LO1
        self.LO1_applicable = False
        self.LO1_value_level = None

# LO2
        self.LO2_applicable = False
        self.LO2_value_level = None


        # Note e conditions
        self.internal_system_hazard = False

        self.environmental_hazard = False

        self.pv_dc_fire_risk = False

        self.RT = 1e-5
        self.FT = 5e-2


        self.annex_E_applicable = False

        self.annex_E_scenario = None
        # options:
        # "explosion_overpressure"
        # "thermal_flux"
        # "toxic_fumes"
        # "soil_pollution"
        # "water_pollution"
        # "radioactive_material"

        self.annex_E_spread_area = None
        # "inside_site_fence" or "outside_site_fence"

        self.annex_E_surrounding_types = []
        # example: ["residences"] or ["roads", "residences"]

        self.fire_explosion_can_injure_surroundings = False
        self.fire_explosion_can_damage_surroundings = False
        self.internal_failure_can_injure_surroundings = False
        self.internal_failure_can_damage_surroundings = False
