from models.building import BuildingInput
from models.zone import Zone
from models.line import Line
from modules.p_module import PModule

def create_office_annex_f():

    building = BuildingInput()
    building.NSG = 4
    building.k = 2
    building.L = 20
    building.W = 40
    building.H = 25

    # paste hv_power_line, lv_power_line, telecom_line here
    # then:


    hv_power_line = Line()

    hv_power_line.service = "power"
    hv_power_line.installation = "buried"
    hv_power_line.type = "hv_transformer_separated"
    hv_power_line.environmental = "suburban"
    hv_power_line.LL = 1000
    hv_power_line.Uw = 2.5
    hv_power_line.spd_level = "none"
    #cld,cli
    hv_power_line.has_external_line = True  #what is this
    hv_power_line.isolating_interface_protected = False
    hv_power_line.lightning_protective_routing = False
    hv_power_line.shielded = False #PLD
    hv_power_line.same_bonding_bar = False
    hv_power_line.multi_grounded_neutral = False
    #ks
    #power_line.routing_precaution = 
    hv_power_line.same_bonding_bar = False

    #PEB
    hv_power_line.equipotential_bonding_level = "none"

    #power_line.internal_system_id = 
    hv_power_line.shield_resistance = False
    hv_power_line.external_cable = "metallic"


    lv_power_line = Line()

    lv_power_line.service = "power"
    lv_power_line.installation = "buried"
    lv_power_line.type = "lv_telecom_data_hv_with_transformer"
    lv_power_line.environmental = "suburban"
    lv_power_line.LL = 100
    lv_power_line.Uw = 2.5
    lv_power_line.spd_level = "none"
    #cld,cli
    lv_power_line.has_external_line = True  #what is this
    lv_power_line.isolating_interface_protected = False
    lv_power_line.lightning_protective_routing = False
    lv_power_line.shielded = False
    lv_power_line.same_bonding_bar = False
    lv_power_line.multi_grounded_neutral = False
    #ks
    #power_line.routing_precaution = 
    lv_power_line.same_bonding_bar = False

    #PEB
    lv_power_line.equipotential_bonding_level = "none"
    lv_power_line.external_cable = "metallic"

    #power_line.internal_system_id = 
    lv_power_line.shield_resistance = False

    telecom_line = Line()

    telecom_line.service = "telecom"
    #telecom_line.installation = "aerial"
    # telecom_line.type = "lv_or_telecom"
    # telecom_line.environmental = "rural"
    telecom_line.LL = 0
    telecom_line.Uw = 1.5
    telecom_line.spd_level = "none"
    telecom_line.has_external_line = True
    telecom_line.isolating_interface_protected = False
    telecom_line.lightning_protective_routing = False
    telecom_line.shielded = False
    telecom_line.same_bonding_bar = False
    telecom_line.multi_grounded_neutral = False
    #ks
    #power_line.routing_precaution = 
    telecom_line.same_bonding_bar = False
    #power_line.mesh_bonding_network = 
    #power_line.equipotential_bonding_spd = 
    #PEB
    telecom_line.equipotential_bonding_level = "none"

    #power_line.internal_system_id = 
    telecom_line.shield_resistance = False
    telecom_line.external_cable = "fibre_optic"

    building.lines = [
            hv_power_line,
            lv_power_line,
            telecom_line
            
    ]
    # Zones
    # =====================================
    # ZONE 1 — CHARACTERISTICS
    # =====================================
    z1 = Zone("Z1")

    # =====================================
    # PEOPLE / OCCUPANCY
    # =====================================
    z1.people_present = True
    z1.tz = 175
    z1.te = 0
    z1.people_exposed_on_structure = True

    # =====================================
    # INTERNAL SYSTEM
    # =====================================
    z1.internal_system_present = False

    # =====================================
    # TOUCH / ELECTRIC SHOCK PROTECTION
    # =====================================
    z1.floor_type = "marble"
    z1.touch_protection = []

    # =====================================
    # FIRE PROTECTION
    # =====================================
    z1.fire_protection = []

    # =====================================
    # FIRE / EXPLOSION RISK
    # =====================================
    z1.fire_risk = "none"
    z1.explosion_zone = False
    z1.lithium_battery_zone = False

    # =====================================
    # EXPLOSION CLASSIFICATION
    # =====================================
    z1.explosion_zone_type = None
    z1.explosive_presence_per_year = None
    z1.negligible_extent = False

    # =====================================
    # STRUCTURAL / LPS CONDITIONS
    # =====================================
    z1.people_in_LPS_area = False
    z1.direct_strike_protected = False
    z1.metal_shelter = False
    z1.lps_protected = False
    z1.natural_lps_structure = False
    z1.internal_system_protected = False

    # =====================================
    # INTERNAL SHIELDING
    # =====================================
    z1.internal_shielding = False
    z1.wm2 = None
    z1.continuous_internal_shield = False

    # =====================================
    # INTERNAL WIRING
    # No internal systems in Z1
    # =====================================
    z1.power_internal_wiring = None
    z1.telecom_internal_wiring = None

    # =====================================
    # OPERATIONAL STATE
    # =====================================
    z1.operational = True

    # =====================================
    # LOSS FACTORS — ANNEX C
    # =====================================
    z1.loss_category = "low"
  #  z1.zone_loss_type = "low"
   # z1.loss_value_level = "upper"

    z1.LT_applicable = True

    z1.LD_applicable = False
    z1.LD_value_level = None

    z1.LF1_applicable = False
    z1.LF1_value_level = None

    z1.LF2_applicable = False
    z1.LF2_value_level = None

    z1.LO1_applicable = False
    z1.LO1_value_level = None

    z1.LO2_applicable = False
    z1.LO2_value_level = None

    # =====================================
    # TOLERABLE VALUES
    # =====================================
    z1.RT = 1e-5
    z1.FT = None

    # =====================================
    # NOTE e CONDITIONS
    # =====================================
    z1.internal_system_hazard = False
    z1.environmental_hazard = False
    z1.pv_dc_fire_risk = False

    

    z2 = Zone("Z2")

    # =====================================
    # PEOPLE / OCCUPANCY
    # =====================================
    z2.people_present = True
    z2.tz = 18
    z2.te = 0
    z2.people_exposed_on_structure = True
    

    # =====================================
    # INTERNAL SYSTEM
    # =====================================
    z2.internal_system_present = False

    # =====================================
    # TOUCH / ELECTRIC SHOCK PROTECTION
    # =====================================
    z2.floor_type = "asphalt"
    z2.touch_protection = []

    # =====================================
    # FIRE PROTECTION
    # =====================================
    z2.fire_protection = []

    # =====================================
    # FIRE / EXPLOSION RISK
    # =====================================
    z2.fire_risk = "none"
    z2.explosion_zone = False
    z2.lithium_battery_zone = False

    # =====================================
    # EXPLOSION CLASSIFICATION
    # =====================================
    z2.explosion_zone_type = None
    z2.explosive_presence_per_year = None
    z2.negligible_extent = False

    # =====================================
    # STRUCTURAL / LPS CONDITIONS
    # =====================================
    z2.people_in_LPS_area = False
    z2.direct_strike_protected = False
    z2.metal_shelter = False
    z2.lps_protected = False
    z2.natural_lps_structure = False
    z2.internal_system_protected = False

    # =====================================
    # INTERNAL SHIELDING
    # =====================================
    z2.internal_shielding = False
    z2.wm2 = None
    z2.continuous_internal_shield = False

    # =====================================
    # INTERNAL WIRING
    # No internal systems
    # =====================================
    z2.power_internal_wiring = None
    z2.telecom_internal_wiring = None

    # =====================================
    # OPERATIONAL STATE
    # =====================================
    z2.operational = True

    # =====================================
    # LOSS FACTORS — ANNEX C
    # =====================================
    z2.loss_category = "low"
   # z2.zone_loss_type = "low"
    z2.loss_value_level = "upper"

    z2.LT_applicable = True

    z2.LD_applicable = True
    z2.LD_value_level = "upper"

    z2.LF1_applicable = False
    z2.LF1_value_level = None

    z2.LF2_applicable = False
    z2.LF2_value_level = None

    z2.LO1_applicable = False
    z2.LO1_value_level = None

    z2.LO2_applicable = False
    z2.LO2_value_level = None

    # =====================================
    # TOLERABLE VALUES
    # =====================================
    z2.RT = 1e-5
    z2.FT = None

    # =====================================
    # NOTE e CONDITIONS
    # =====================================
    z2.internal_system_hazard = False
    z2.environmental_hazard = False
    z2.pv_dc_fire_risk = False

    z3 = Zone("Z3")

    # =====================================
    # PEOPLE / OCCUPANCY
    # =====================================
    z3.people_present = True              # PO — presence of people
    z3.tz = 440                          # tz — presence time per year (hours)
    z3.te = 8760
    z3.people_exposed_on_structure = True                          # te — equipment exposure time per year
    # =====================================
    # INTERNAL SYSTEM
    # =====================================
    z3.internal_system_present = True     # internal system/equipment exists
    # ====================================
    # TOUCH / ELECTRIC SHOCK PROTECTION
    # =====================================
    z3.floor_type = "linoleum"            # rt — reduction factor (floor type)
    z3.touch_protection = [               # Pam — protection measures
        #"warning_notice",
        #"electrical_insulation"
    ]
    # =====================================
    # FIRE PROTECTION
    # =====================================
    z3.fire_protection = [                # rP — fire protection measures
        #"extinguishers",
        "automatic_alarm"
    ]
    # =====================================
    # FIRE / EXPLOSION RISK
    # =====================================
    z3.fire_risk = "high"                  # rp — fire risk
    z3.explosion_zone = False             # rp special condition
    z3.lithium_battery_zone = False       # rp special condition
    # =====================================
    # EXPLOSION CLASSIFICATION
    #=====================================
    z3.explosion_zone_type = None         # rf — hazardous zone classification
    z3.explosive_presence_per_year = None # rf note 7
    z3.negligible_extent = False          # rf note 7 reduction condition
    # =====================================
    # STRUCTURAL / LPS CONDITIONS
    # =====================================
    z3.people_in_LPS_area = False
    z3.direct_strike_protected = False    # rf
    z3.metal_shelter = False              # rf related
    z3.lps_protected = False              # rf
    z3.natural_lps_structure = False      # rf
    z3.internal_system_protected = False  # rfrelated
    # =====================================
    # INTERNAL SHIELDING
    # =====================================
    z3.internal_shielding = False         # KS2 — internal shielding
    z3.wm2 = None                         # KS2 — mesh width
    z3.continuous_internal_shield = False # KS2
    # =====================================
    # INTERNAL WIRING
    # =====================================
    z3.power_internal_wiring = (
        "unshielded_same_conduit"
    )                                      # KS3P
    z3.telecom_internal_wiring = (
        "unshielded_no_routing_precaution"
    )                                      # KS3T
    # =====================================
    # OPERATIONAL STATE
    # =====================================
    z3.operational = True
    # =====================================
    # LOSS FACTORS — ANNEX C
    # =====================================
    z3.loss_category = "normal"

    z3.LT_applicable = True               # LT
    z3.LD_applicable = False              # LD
    z3.LD_value_level = None
    # LF1
    z3.LF1_applicable = True              # LF1
    z3.LF1_value_level = "upper"
    # LF2
    z3.LF2_applicable = True              # LF2
    z3.LF2_value_level = "upper"
    # LO1
    z3.LO1_applicable = False             # LO1
    z3.LO1_value_level = None
    # LO2
    z3.LO2_applicable = False             # LO2
    z3.LO2_value_level = None


    # =====================================
    # NOTE e CONDITIONS
    # =====================================
    z3.internal_system_hazard = False
    z3.environmental_hazard = False
    z3.pv_dc_fire_risk = False

    z3.annex_E_applicable = True

    z3.annex_E_scenario = "explosion_overpressure"

    z3.annex_E_spread_area = "outside_site_fence"

    z3.annex_E_surrounding_types = [
        #"roads",
        "pedestrian_ways"
    ]

    z3.fire_explosion_can_injure_surroundings = True

    z3.fire_explosion_can_damage_surroundings = True

    z3.internal_failure_can_injure_surroundings = True

    z3.internal_failure_can_damage_surroundings = True

    z4 = Zone("Z4")

    # =====================================
    # PEOPLE / OCCUPANCY
    # =====================================
    z4.people_present = True              # PO — presence of people
    z4.tz = 2630                          # tz — presence time per year (hours)
    z4.te = 8760
    z4.people_exposed_on_structure = True                         # te — equipment exposure time per year
    # =====================================
    # INTERNAL SYSTEM
    # =====================================
    z4.internal_system_present = True     # internal system/equipment exists
    # ====================================
    # TOUCH / ELECTRIC SHOCK PROTECTION
    # =====================================
    z4.floor_type = "linoleum"            # rt — reduction factor (floor type)
    z4.touch_protection = [               # Pam — protection measures
        #"warning_notice",
        # "electrical_insulation"
    ]
    # =====================================
    # FIRE PROTECTION
    # =====================================
    z4.fire_protection = [                # rP — fire protection measures
        "extinguishers",
        # "automatic_alarm"
    ]
    # =====================================
    # FIRE / EXPLOSION RISK
    # =====================================
    z4.fire_risk = "low"                  # rf — fire risk
    z4.explosion_zone = False             # rf special condition
    z4.lithium_battery_zone = False       # rf special condition
    # =====================================
    # EXPLOSION CLASSIFICATION
    #=====================================
    z4.explosion_zone_type = None         # rf — hazardous zone classification
    z4.explosive_presence_per_year = None # rf note 7
    z4.negligible_extent = False          # rf note 7 reduction condition
    # =====================================
    # STRUCTURAL / LPS CONDITIONS
    # =====================================
    z4.direct_strike_protected = False    # PB / PC related
    z4.metal_shelter = False              # PB related
    z4.lps_protected = False              # PLPS
    z4.natural_lps_structure = False      # PLPS natural component
    z4.internal_system_protected = False  # PC / PM related

    z4.people_in_LPS_area = False
    # =====================================
    # INTERNAL SHIELDING
    # =====================================
    z4.internal_shielding = False         # KS2 — internal shielding
    z4.wm2 = None                         # KS2 — mesh width
    z4.continuous_internal_shield = False # KS2
    # =====================================
    # INTERNAL WIRING
    # =====================================
    z4.power_internal_wiring = (
        "unshielded_same_conduit"
    )                                      # KS3P
    z4.telecom_internal_wiring = (
        "unshielded_no_routing_precaution"
    )                                      # KS3T
    # =====================================
    # OPERATIONAL STATE
    # =====================================
    z4.operational = True
    # =====================================
    # LOSS FACTORS — ANNEX C
    # =====================================
    z4.LT_applicable = True               # LT
    z4.LD_applicable = False              # LD
    z4.LD_value_level = None
    # LF1
    z4.LF1_applicable = True              # LF1
    z4.LF1_value_level = "upper"
    # LF2
    z4.LF2_applicable = True              # LF2
    z4.LF2_value_level = "upper"
    # LO1
    z4.LO1_applicable = False             # LO1
    z4.LO1_value_level = None
    # LO2
    z4.LO2_applicable = False             # LO2
    z4.LO2_value_level = None
    # =====================================
    # NOTE e CONDITIONS
    # =====================================
    z4.internal_system_hazard = False
    z4.environmental_hazard = False
    z4.pv_dc_fire_risk = False
    z4.loss_category = "normal"     

    # =====================================
    # Z5 — COMPUTER CENTRE
    # =====================================

    z5 = Zone("Z5")

    # =====================================
    # PEOPLE / OCCUPANCY
    # =====================================
    z5.people_present = True
    z5.tz = 2200
    z5.te = 8760
    z5.people_exposed_on_structure = False

    # =====================================
    # INTERNAL SYSTEM
    # =====================================
    z5.internal_system_present = True

    # =====================================
    # TOUCH / ELECTRIC SHOCK PROTECTION
    # =====================================
    z5.floor_type = "linoleum"
    z5.touch_protection = []

    # =====================================
    # FIRE PROTECTION
    # =====================================
    z5.fire_protection = [
        "automatic_alarm"
    ]

    # =====================================
    # FIRE / EXPLOSION RISK
    # =====================================
    z5.fire_risk = "low"
    z5.explosion_zone = False
    z5.lithium_battery_zone = False

    # =====================================
    # EXPLOSION CLASSIFICATION
    # =====================================
    z5.explosion_zone_type = None
    z5.explosive_presence_per_year = None
    z5.negligible_extent = False

    # =====================================
    # STRUCTURAL / LPS CONDITIONS
    # =====================================
    z5.people_in_LPS_area = False
    z5.direct_strike_protected = False
    z5.metal_shelter = False
    z5.lps_protected = False
    z5.natural_lps_structure = False
    z5.internal_system_protected = False

    # =====================================
    # INTERNAL SHIELDING
    # =====================================
    z5.internal_shielding = False
    z5.wm2 = None
    z5.continuous_internal_shield = False

    # =====================================
    # INTERNAL WIRING
    # =====================================
    z5.power_internal_wiring = "unshielded_same_conduit"
    z5.telecom_internal_wiring = "unshielded_different_routing"

    # =====================================
    # OPERATIONAL STATE
    # =====================================
    z5.operational = True

    # =====================================
    # LOSS FACTORS — ANNEX C
    # =====================================
    z5.loss_category = "high"
    z5.zone_loss_type = "high"
  #  z5.loss_value_level = "upper"

    z5.LT_applicable = True

    z5.LD_applicable = False
    z5.LD_value_level = None

    z5.LF1_applicable = True
    z5.LF1_value_level = "upper"

    z5.LF2_applicable = True
    z5.LF2_value_level = "upper"

    z5.LO1_applicable = False
    z5.LO1_value_level = None

    z5.LO2_applicable = False
    z5.LO2_value_level = None

    # =====================================
    # TOLERABLE VALUES
    # =====================================
    z5.RT = 1e-5
    z5.FT = 5e-2

    # =====================================
    # NOTE e CONDITIONS
    # =====================================
    z5.internal_system_hazard = False
    z5.environmental_hazard = False
    z5.pv_dc_fire_risk = False 
    
    building.zones = [
        z1,
        z2,
        z3,
        z4,
        z5
    ]

    for zone in building.zones:
        zone.Pp = PModule.calculate_Pp(building, zone)
        zone.Pe = PModule.calculate_Pe(zone)

    return building