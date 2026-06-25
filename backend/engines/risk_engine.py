from modules.n_module import NModule
from modules.p_module import PModule
from modules.l_module import LModule

from engines.component_applicability import ComponentApplicability

from utils.formulas import risk_component

class RiskEngine:

    @staticmethod
    def calculate_R(inputs):

        ND  = NModule.ND(inputs)
        NM  = NModule.NM(inputs)
        NModule.NL(inputs)
        NModule.NI(inputs)
       # NL  = NModule.NL(inputs)
       # NI  = NModule.NI(inputs)
        NDJ = NModule.NDJ(inputs)

        zone_results = {} 

        for zone in inputs.zones:
            def calc_if(applicable, value):
                if applicable:
                    return value
                return 0

            ComponentApplicability.apply(zone)

    # calculate risk components

            # S1
            RAT = calc_if(
                zone.RAT_applicable,
                risk_component(ND, PModule.PAT(inputs, zone), LModule.calculate_LT(zone), zone.Pp)
            )

            RAD = calc_if(
                zone.RAD_applicable,
                risk_component(ND, PModule.PAD(inputs, zone), LModule.calculate_LD(zone), zone.Pp)
            )

            RB1 = calc_if(
                zone.RB_applicable,
                risk_component(ND, PModule.PB(inputs, zone), LModule.calculate_LF1(zone), zone.Pp)
            )

            RB2 = calc_if(
                zone.RB_applicable,
                risk_component(ND, PModule.PB(inputs, zone), LModule.calculate_LF2(zone))
            )
                       
# =========================
# RC — mixed-service logic
# =========================

            PC_values = []
            services = set()

            for line in inputs.lines:

                services.add(line.service)

                # Skip if the internal system for this service is not metallic/present.
                # (Office: telecom external fibre but internal copper -> still present.
                #  Hospital: telecom external+internal fibre -> not present -> skip.)
                if line.service == "power" and not getattr(zone, "has_power_internal_system", True):
                    continue
                if line.service == "telecom" and not getattr(zone, "has_telecom_internal_system", True):
                    continue

                PC = PModule.PC(
                    inputs,
                    zone,
                    line
                )

                if PC > 0:

                    PC_values.append(PC)

# Same service only
# use representative/highest value

            if len(services) == 1:

                PC_total = max(PC_values) if PC_values else 0

# Different services
# use IEC probabilistic combination

            else:

                PC_combined = 1

                for pc in PC_values:

                    PC_combined *= (1 - pc)

                PC_total = 1 - PC_combined

            print("PC_values =", PC_values)
            print("PC_total =", PC_total)

            if zone.RC_applicable:

                RC1 = risk_component(

                    ND,

                    PC_total,

                    LModule.calculate_LO1(zone),

                    zone.Pp,

                    zone.Pe
                )

                RC2 = risk_component(

                    ND,

                    PC_total,

                    LModule.calculate_LO2(zone),

                    zone.Pe
                )

                RC1_line = risk_component(

                    ND,

                    PC,

                    LModule.calculate_LO1(zone),

                    zone.Pp,

                    zone.Pe
                )

                RC2_line = risk_component(

                    ND,

                    PC,

                    LModule.calculate_LO2(zone),

                    zone.Pe
                )

            else:
                RC1 = 0
                RC2 = 0    

               # print("\n===== RC LINE DEBUG =====")

                #print("Service =", line.service)

                #print("Type =", line.type)

                #print("PC =", PC)

                #print("RC1 contribution =", RC1_line)

                #print("RC2 contribution =", RC2_line)
            

            # S2
            # =========================
            # RM — mixed-service logic
            # =========================
            PM_values = []
            services = set()

            for line in inputs.lines:

                services.add(line.service)

                if line.service == "power":

                    if not getattr(zone, "has_power_internal_system", True):
                        continue

                    PM = PModule.PM_power(
                        inputs,
                        zone,
                        line
                    )

                else:

                    if not getattr(zone, "has_telecom_internal_system", True):
                        continue

                    PM = PModule.PM_telecom(
                        inputs,
                        zone,
                        line
                    )

                if PM > 0:

                    PM_values.append(PM)

# Same service only
# use representative/highest value

            if len(services) == 1:

                PM_total = max(PM_values) if PM_values else 0

# Different services
# use IEC probabilistic combination

            else:

                PM_combined = 1

                for pm in PM_values:

                    PM_combined *= (1 - pm)

                PM_total = 1 - PM_combined

            print("PM_values =", PM_values)
            print("PM_total =", PM_total)

            if zone.RM_applicable:

                RM1 = risk_component(

                    NM,

                    PM_total,

                    LModule.calculate_LO1(zone),

                    zone.Pe,

                    zone.Pp
                )

                RM2 = risk_component(

                    NM,

                    PM_total,

                    LModule.calculate_LO2(zone),

                    zone.Pe
                )
            else:
                RM1 = 0
                RM2 = 0

            # S3
           # =========================
            # RU — IEC worst-case selection
            # =========================

            if zone.RU_applicable:
                RU_values = []


                for line in inputs.lines:

                    RU_line = risk_component(

                        line.NL + line.NDJ,

                        PModule.PU(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LT(zone),

                        zone.Pp
                    )

                    RU_values.append(RU_line)


                RU = sum(RU_values)

            else:
                RU = 0   

            # =========================
            # RV — IEC worst-case selection
            # =========================

            if zone.RV_applicable:

                RV1_values = []
                RV2_values = []


                for line in inputs.lines:

                    RV1_line = risk_component(

                        line.NL + line.NDJ,

                        PModule.PV(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LF1(zone),

                        zone.Pp
                    )

                    RV2_line = risk_component(

                        line.NL + line.NDJ,

                        PModule.PV(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LF2(zone),

                    )

                    RV1_values.append(RV1_line)
                    RV2_values.append(RV2_line)


                RV1 = sum(RV1_values)

                RV2 = sum(RV2_values)

            else:
                RV1 = 0
                RV2 = 0    

            if zone.RW_applicable:
                RW1_values = []
                RW2_values = []


                for line in inputs.lines:

                    RW1_line = risk_component(

                        line.NL + line.NDJ,

                        PModule.PW(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LO1(zone),
                        zone.Pe,
                        zone.Pp

                    )

                    RW2_line = risk_component(

                        line.NL + line.NDJ,

                        PModule.PW(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LO2(zone),

                        zone.Pe
                    )

                    RW1_values.append(RW1_line)
                    RW2_values.append(RW2_line)


                RW1 = sum(RW1_values)

                RW2 = sum(RW2_values)
            else:
                RW1 = 0
                RW2 = 0    

            # S4
            # =========================
            # RZ — IEC worst-case selection
            # =========================
            if zone.RZ_applicable:
                RZ1_values = []

                RZ2_values = []

                for line in inputs.lines:

                    RZ1_line = risk_component(

                        line.NI,

                        PModule.PZ(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LO1(zone),

                        zone.Pe,

                        zone.Pp
                    )

                    RZ2_line = risk_component(

                        line.NI,

                        PModule.PZ(
                            inputs,
                            zone,
                            line
                        ),

                        LModule.calculate_LO2(zone),

                        zone.Pe
                    )

                    RZ1_values.append(RZ1_line)

                    RZ2_values.append(RZ2_line)

                RZ1 = sum(RZ1_values)

                RZ2 = sum(RZ2_values)

            else:
                RZ1 = 0
                RZ2 = 0    

            RL1_zone = (RAT + RAD+ RB1 + RC1 + RM1 + RU + RV1 + RW1 + RZ1)
            RL2_zone = (RB2 + RC2 + RM2 + RV2 + RW2 + RZ2)

            R_total = RL1_zone + RL2_zone
            RT = zone.RT

            if R_total > RT:
                risk_status = "Protection required"
            else:
                risk_status = "Protection not required"

    
            zone_results[zone.name] = {

                "RAT": RAT,
                "RAD": RAD,
                "RB1": RB1,
                "RB2": RB2,
                "RC1": RC1,
                "RC2": RC2,
                "RM1": RM1,
                "RM2": RM2,
                "RU": RU,
                "RV1": RV1,
                "RV2": RV2,
                "RW1": RW1,
                "RW2": RW2,
                "RZ1": RZ1,
                "RZ2": RZ2,

                "RL1": RL1_zone,
                "RL2": RL2_zone,

                "R_total": R_total,
                "RT": RT,
                "risk_status": risk_status
            }
           # RL1_total += RL1_zone
           # RL2_total += RL2_zone

       #     print(f"\n===== {zone.name} =====")

       #     print("RL1 =", RL1_zone)

        #    print("RL2 =", RL2_zone)

         #   print("R_total =", RL1_zone + RL2_zone)

        return zone_results