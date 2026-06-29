from mappings.mapping import Mapping
import math

class PModule:
    @staticmethod
    def calculate_Pam(inputs, zone):

        touch_protection = getattr(zone, "touch_protection", [])

        if not touch_protection:
            touch_protection = ["none"]

        if "access_restriction" in touch_protection:
            return 0

        Pam = 1

        for measure in touch_protection:
            Pam *= Mapping.Pam.get(measure, 1)

        # Annex B Note 3 - Natural LPS
        if PModule.natural_lps_present(inputs):
            Pam *= Mapping.Pam["natural_lps"]

        return Pam


    @staticmethod
    def natural_down_conductor_present(inputs):

        return (
            inputs.extensive_metal_framework
            or inputs.reinforced_concrete_interconnected
        )
    

    @staticmethod
    def calculate_PLPS(inputs):

        if inputs.LPS_class is None:
            return 1

        if (
            inputs.LPS_class == "I"
            and inputs.metal_roof
            and inputs.complete_roof_protection
            and PModule.natural_down_conductor_present(inputs)
        ):
            return Mapping.PLPS["I_metal_roof"]

        if (
            inputs.LPS_class == "I"
            and PModule.natural_down_conductor_present(inputs)
        ):
            return Mapping.PLPS["I_natural"]

        return Mapping.PLPS.get(inputs.LPS_class, 1)
    
    @staticmethod
    def natural_lps_present(inputs):

        return(
            inputs.extensive_metal_framework
            or inputs.reinforced_concrete_interconnected
            or (
                inputs.mesh_earth_termination
               and not inputs.accessible_metal_installation
            )
        )
    
    @staticmethod
    def calculate_PS(inputs):

     # NOTE 1 — LPS installed → PS = 1
        if inputs.LPS_class is not None:
            return 1

    # Base values from table
        wall_PS = Mapping.PS.get(inputs.wall_material, 1)
        roof_PS = Mapping.PS.get(inputs.roof_material, 1)

    # NOTE 3 — use larger value
        PS = max(wall_PS, roof_PS)

    # NOTE 4 — reinforced concrete condition
        if inputs.wall_material == "reinforced_concrete":
            if not inputs.reinforcement_interconnected:
                PS = 1

        if inputs.roof_material == "reinforced_concrete":
            if not inputs.reinforcement_interconnected:
                PS = 1

    # NOTE 2 — unbonded metal parts
        if inputs.unbonded_metal_parts:
            PS = 1

        return PS
    
    @staticmethod
    def calculate_rP(zone):

        if zone.lithium_battery_zone:
            return 1

        if zone.explosion_zone:
            return 1

        fire_protection = getattr(zone, "fire_protection", [])

        if not fire_protection or "none" in fire_protection:
            return 1

        values = [
            Mapping.rP.get(p, 1)
            for p in fire_protection
        ]

        return min(values)
    
    @staticmethod
    def calculate_rf(zone):

        values = []

        explosion_ignored = (
            (zone.explosive_presence_per_year is not None
             and zone.explosive_presence_per_year < 0.1)
            or zone.negligible_extent
            or zone.direct_strike_protected
            or zone.metal_shelter
            or zone.lps_protected
            or zone.natural_lps_structure
            or zone.internal_system_protected
        )

        if zone.explosion_zone_type and not explosion_ignored:
            values.append(
                Mapping.rF_explosion.get(zone.explosion_zone_type, 0)
            )

        if zone.fire_risk:
            values.append(
                Mapping.rF_fire.get(zone.fire_risk, 0) 
            )

        if not values:
            return 0

        return max(values)
    
    @staticmethod
    def calculate_PSPD(inputs, line, zone, source):

        if line.service == "power":

            if getattr(zone, "power_use_custom_pspd", False):
                return (
                    zone.power_custom_pspd
                    if zone.power_custom_pspd is not None
                    else 1
                )

            spd_level = getattr(zone, "power_spd_level", "none")
            table = Mapping.PSPD_POWER

        elif line.service == "telecom":

            if getattr(zone, "telecom_use_custom_pspd", False):
                return (
                    zone.telecom_custom_pspd
                    if zone.telecom_custom_pspd is not None
                    else 1
                )

            spd_level = getattr(zone, "telecom_spd_level", "none")
            table = Mapping.PSPD_TELECOM

        else:
            raise ValueError("Invalid line service for PSPD")

        if source not in table:
            raise ValueError("Invalid source of damage for PSPD")

        # "better than LPL I" levels are only tabulated for some sources
        # (S3 and S4 per Annex B Table B.7/B.8). For sources that do not have
        # these entries (S1, S2 inductive coupling), fall back to the strongest
        # defined level ("I"), since a better-than-LPL-I SPD is at least as good.
        if (
            isinstance(spd_level, str)
            and spd_level.startswith("better")
            and spd_level not in table[source]
        ):
            return table[source]["I"]

        if spd_level not in table[source]:
            raise ValueError(
                f"SPD level '{spd_level}' is not valid for source {source}"
            )

        return table[source][spd_level]
   

    @staticmethod
    def calculate_CLD(line):

        # Annex B Table B.9: "No external line or optical line" -> CLD = 0
        if getattr(line, "external_cable", "metallic") == "fibre_optic":
            return 0

        if not line.has_external_line:
            return 0

        if line.isolating_interface_protected:
            return 0

        if line.lightning_protective_routing:
            return 0

        return 1
    
    @staticmethod
    def calculate_CLI(line):

        # Annex B Table B.9: "No external line or optical line" -> CLI = 0
        if getattr(line, "external_cable", "metallic") == "fibre_optic":
            return 0

        if not line.has_external_line:
            return 0

        if line.isolating_interface_protected:
            return 0

        if line.lightning_protective_routing:
            return 0

        if (
            line.shielded
            and
            line.same_bonding_bar
        ):
            return 0

        if (
            line.shielded
            and
            not line.same_bonding_bar
            and
            line.installation == ["buried", "buried_mesh"]
        ):
            return 0.3

        if (
            line.shielded
            and
            not line.same_bonding_bar
            and
            line.installation == "aerial"
        ):
            return 0.1

        if line.multi_grounded_neutral:
            return 0.2

        return 1
    
    @staticmethod
    def calculate_KS1(inputs):

    # ------------------------------
    # No shielding
    # ------------------------------
        if inputs.wm1 is None:
            return 1

    # Continuous metal shield
    # IEC special case
    
        if inputs.continuous_metal_shield:

            KS1 = 1e-4
    
        else:

            KS1 = 0.12 * inputs.wm1

    # Meshed bonding network
    
        if inputs.meshed_bonding_network:

            KS1 *= 0.5

    # IEC maximum
   
        KS1 = min(KS1, 1)

        return KS1
    

    @staticmethod
    def calculate_KS2(inputs, zone):

        if zone.wm2 is None:
            return 1

        if zone.continuous_metal_shield:

            KS2 = 1e-4

        else:

            KS2 = 0.12 * zone.wm2

        if zone.meshed_bonding_network:

            KS2 *= 0.5

        KS2 = min(KS2, 1)

        return KS2

    @staticmethod
    def calculate_KS3_power(zone):

        if zone.power_internal_wiring is None:
            return 0

        return Mapping.KS3.get(
            zone.power_internal_wiring,
            1
        )


    @staticmethod
    def calculate_KS3_telecom(zone):

        if zone.telecom_internal_wiring is None:
            return 0

        return Mapping.KS3.get(
            zone.telecom_internal_wiring,
            1
        )
    
    @staticmethod
    def calculate_PMS_power(inputs, zone):

        #if not zone.has_power_internal_system:
           # return 0

        KS1 = PModule.calculate_KS1(
            inputs
        )

        KS2 = PModule.calculate_KS2(
            inputs,
            zone
        )

        KS3 = PModule.calculate_KS3_power(
            zone
        )

        PMS = (KS1 * KS2 * KS3) ** 2
      #  print("\n--- PMS Power Debug ---")
      #  print("KS1:", KS1)
      #  print("KS2:", KS2)
      #  print("KS3P:", KS3)

      #  print("PMS:", PMS)

        return PMS

    

    @staticmethod
    def calculate_PMS_telecom(inputs, zone):

        #if not zone.has_telecom_internal_system:
            #return 0

        KS1 = PModule.calculate_KS1(
            inputs
        )

        KS2 = PModule.calculate_KS2(
            inputs,
            zone
        )

        KS3 = PModule.calculate_KS3_telecom(
            zone
        )
        PMS = (KS1 * KS2 * KS3) ** 2


      #  print("\n--- PMS Telecom Debug ---")
      #  print("KS1:", KS1)
      #  print("KS2:", KS2)
      #  print("KS3T:", KS3)
      #  print("PMS:", PMS)

        return PMS

    @staticmethod
    def calculate_PLD(line):

        if (
            not line.shielded
            or not line.same_bonding_bar
        ):
            category = "unshielded"
        else:
            category = line.shield_resistance or "unshielded"

        if line.Uw <= 12:
            table = Mapping.PLD_LOW
        else:
            table = Mapping.PLD_HIGH

        return table.get(
            category,
            table["unshielded"]
        ).get(
            line.Uw,
            1
        )
    
    @staticmethod
    def calculate_PEB(line):

        PEB = Mapping.PEB.get(

            line.equipotential_bonding_level,

            1
        )

        # print("\n--- PEB Debug ---")

        # print(
        #     "Equipotential bonding:",
        #     line.equipotential_bonding_level
        # )

        # print("PEB:", PEB)

        return PEB
    

    @staticmethod
    def calculate_Pp(inputs, zone):

    # IEC NOTE 1
        if zone.tz is None:
            return 1

        Pp = zone.tz / 8760

    # IEC NOTE 2
        if inputs.TWS:
            Pp *= inputs.PTWS

    #     print("\n--- Pp Debug ---")
    #  #   print("tz:", zone.tz)
    #  #   print("TWS:", inputs.TWS)
    #  #   print("PTWS:", inputs.PTWS)
    #     print("Pp:", Pp)

        return Pp
    
    @staticmethod
    def calculate_Pe(zone):

    # IEC NOTE 1
        if zone.te is None:
            return 1

        Pe = zone.te / 8760

    #     print("\n--- Pe Debug ---")
    #  #   print("te:", zone.te)
    #     print("Pe:", Pe)

        return Pe



    @staticmethod
    def PAT(inputs, zone):

    # PLPS (Table B.3)
        PLPS = PModule.calculate_PLPS(inputs)

    # Pam (Table B.1)
        Pam = PModule.calculate_Pam(inputs, zone)

    # rt (Table B.2)
        rt = Mapping.rt.get(zone.floor_type, 1)

    # PTWS (default = 1)
        PTWS = inputs.PTWS if inputs.TWS else 1

    # Final PAT
        PAT = PLPS * Pam * rt * PTWS

      #  print("\n--- PAT Debug ---")
      #  print("PLPS:", PLPS)
      #  print("Pam:", Pam)
      #  print("rt:", rt)
      #  print("PTWS:", PTWS)
      #  print("PAT:", PAT)

        return PAT

       

    @staticmethod
    def PAD(inputs, zone):

        # Pam
        Pam = PModule.calculate_Pam(inputs, zone)

        # PO (people presence)
        PO = 1 if zone.people_present else 0

        # PLPS
        PLPS = PModule.calculate_PLPS(inputs)

        # PTWS
        PTWS = inputs.PTWS if inputs.TWS else 1

        # NOTE 2 — TWS overrides Pam
        if inputs.TWS:
            Pam = 1

        # NOTE 3 — people not in LPS area
        if not zone.people_in_LPS_area:
            PLPS = 1

        # Final PAD
        PAD = PTWS * Pam * PO * PLPS

      #  print("--- PAD Debug ---")
     #   print("PTWS:", PTWS)
      #  print("Pam:", Pam)
      #  print("PO:", PO)
      #  print("PLPS:", PLPS)
      #  print("PAD:", PAD)

        return PAD
    
    @staticmethod
    def PB(inputs, zone):

        # PS
        PS = PModule.calculate_PS(inputs)

    # PLPS
        PLPS = PModule.calculate_PLPS(inputs)

    # rP
        rP = PModule.calculate_rP(zone)

    # rf
        rf = PModule.calculate_rf(zone)

    # Final PB
        PB = PS * PLPS * rP * rf

      #  print("\n--- PB Debug ---")
      #  print("PS:", PS)
      #  print("PLPS:", PLPS)
      #  print("rP:", rP)
    #    print("rf:", rf)
     #   print("PB:", PB)

        return PB

    @staticmethod
    def PC(inputs, zone, line):

        natural_lps = (
           inputs.reinforced_concrete_interconnected
           or inputs.extensive_metal_framework
        )

        if not (
            inputs.LPS_class is not None
            or natural_lps
        ):
            PSPD = 1
        else:
            PSPD = PModule.calculate_PSPD(
            inputs,
            line,
            zone,
            "S1"
        )

        CLD = PModule.calculate_CLD(
            line
        )

        PC = PSPD * CLD

    #    print("\n--- PC Debug ---")
    #    print("PSPD:", PSPD)
    #    print("CLD:", CLD)
    #    print("PC:", PC)

        return PC

    @staticmethod
    def PM_power(inputs, zone, line):

        
        PSPD = PModule.calculate_PSPD(
            inputs,
            line,
            zone,
            "S2"
        )

        PMS = PModule.calculate_PMS_power(
            inputs,
            zone
        )

        PM = PSPD * PMS

    #    print("\n--- PM Power Debug ---")
    #    print("PSPD:", PSPD)
    #    print("PMS:", PMS)
    #    print("PM:", PM)

        return PM
    
    @staticmethod
    def PM_telecom(inputs, zone, line):

        PSPD = PModule.calculate_PSPD(
            inputs,
            line,
            zone,
            "S2"
        )

        PMS = PModule.calculate_PMS_telecom(
            inputs,
            zone
        )

        PM = PSPD * PMS

    #    print("\n--- PM Power Debug ---")
    #    print("PSPD:", PSPD)
    #    print("PMS:", PMS)
    #    print("PM:", PM)

        return PM

    @staticmethod
    def PU(inputs, zone, line):

        Pam = PModule.calculate_Pam(
            inputs,
            zone
        )

  
        PEB = PModule.calculate_PEB(
            line
        )


        PLD = PModule.calculate_PLD(
            line
        )

        PTWS = (
            inputs.PTWS
            if inputs.TWS
            else 1
        )


        CLD = PModule.calculate_CLD(
            line
        )


        rt = Mapping.rt.get(

            zone.floor_type,

            1
        )


        PU = Pam * PEB * PLD * PTWS * CLD * rt

    #    print("\n--- PU Debug ---")
     #   print("Pam:", Pam)
    #    print("PEB:", PEB)
    #    print("PLD:", PLD)
    #    print("PTWS:", PTWS)
    #    print("CLD:", CLD)
    #    print("rt:", rt)
    #    print("PU:", PU)

        return PU

    @staticmethod
    def PV(inputs, zone, line):

    # ------------------------------
    # PEB
    # ------------------------------
        PEB = PModule.calculate_PEB(
            line
        )

        PLD = PModule.calculate_PLD(
            line
        )

        PTWS = (
            inputs.PTWS
            if inputs.TWS
            else 1
        )

 
        CLD = PModule.calculate_CLD(
            line
        )


        rf = PModule.calculate_rf(
            zone
        )

        rp = PModule.calculate_rP(
            zone
        )
        

        PV = PEB * PLD * PTWS * CLD * rf * rp

    #    print("\n--- PV Debug ---")
    #    print("PEB:", PEB)
    #    print("PLD:", PLD)
    #    print("PTWS:", PTWS)
    #    print("CLD:", CLD)
    #    print("rf:", rf)
    #    print("rp:", rp)
    #    print("PV:", PV)

        return PV
    
    @staticmethod
    def PW(inputs, zone, line):

        

        PSPD = PModule.calculate_PSPD(
            inputs,
            line,
            zone,
            "S3"
        )

       
        PTWS = (
            inputs.PTWS
            if inputs.TWS
            else 1
        )
        
        PLD = PModule.calculate_PLD(line)

        CLD = PModule.calculate_CLD(line)


        PW = (
            PSPD
            *PTWS
            * PLD
            * CLD
        )

      #  print("\n--- PW Debug ---")

      #  print("Service:", line.service)
      #  print("PSPD:", PSPD)
      #  print("PTWS:", PTWS)
      #  print("PLD:", PLD)
      #  print("CLD:", CLD)
      #  print("PW:", PW)

        return PW

    @staticmethod
    def PZ(inputs, zone, line):


        PSPD = PModule.calculate_PSPD(
            inputs,
            line,
            zone,
            "S4"
        )

        PTWS = inputs.PTWS if inputs.TWS else 1

        CLI = PModule.calculate_CLI(
            line
        )

        PZ = PSPD * PTWS * CLI

    # ------------------------------
    # Debug
    # ------------------------------
       # print("\n--- PZ Debug ---")
       # print("Service:", line.service)
       # print("PSPD:", PSPD)
      #  print("PTWS:", PTWS)
       # print("CLI:", CLI)
       # print("PZ:", PZ)

        return PZ