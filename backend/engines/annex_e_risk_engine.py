from modules.n_module import NModule
from modules.p_module import PModule
from modules.annex_e_module import AnnexEModule
class AnnexERiskEngine:

    @staticmethod
    def calculate_RE(inputs):

        ND = NModule.ND(inputs)
        NM = NModule.NM(inputs)

        # Create line.NL and line.NI
        NModule.NL(inputs)
        NModule.NI(inputs)

        NDJ = NModule.NDJ(inputs)

        annex_E_results = {}

        for zone in inputs.zones:

            if not zone.annex_E_applicable:
                annex_E_results[zone.name] = {
                    "RB1E": 0,
                    "RB2E": 0,
                    "RC1E": 0,
                    "RC2E": 0,
                    "RM1E": 0,
                    "RM2E": 0,
                    "RV1E": 0,
                    "RV2E": 0,
                    "RW1E": 0,
                    "RW2E": 0,
                    "RZ1E": 0,
                    "RZ2E": 0,
                    "RE1": 0,
                    "RE2": 0,
                    "RE_total": 0
                }
                continue

            # =========================
            # ANNEX E LOSS VALUES
            # =========================

            PPE = AnnexEModule.calculate_PPE(zone)

            LF1E = AnnexEModule.calculate_LF1E(
                inputs,
                zone
            )

            LF2E = AnnexEModule.calculate_LF2E(
                zone
            )

            LO1E = AnnexEModule.calculate_LO1E(
                inputs,
                zone
            )

            LO2E = AnnexEModule.calculate_LO2E(
                zone
            )

            Pe = zone.Pe

            # =========================
            # S1 — RB and RC
            # =========================

            PB = PModule.PB(
                inputs,
                zone
            )

            RB1E = (
                ND
                * PB
                * PPE
                * LF1E
            )

            RB2E = (
                ND
                * PB
                * LF2E
            )

            # =========================
            # PC TOTAL — same as RiskEngine
            # =========================

            PC_values = []
            services = set()

            for line in inputs.lines:

                services.add(line.service)

                PC = PModule.PC(
                    inputs,
                    zone,
                    line
                )

                if PC > 0:
                    PC_values.append(PC)

            if len(services) == 1:

                PC_total = max(PC_values) if PC_values else 0

            else:

                PC_combined = 1

                for pc in PC_values:
                    PC_combined *= (1 - pc)

                PC_total = 1 - PC_combined

            RC1E = (
                ND
                * PC_total
                * PPE
                * Pe
                * LO1E
            )

            RC2E = (
                ND
                * PC_total
                * Pe
                * LO2E
            )

            # =========================
            # PM TOTAL — same as RiskEngine
            # =========================

            PM_values = []
            services = set()

            for line in inputs.lines:

                services.add(line.service)

                if line.service == "power":

                    PM = PModule.PM_power(
                        inputs,
                        zone,
                        line
                    )

                else:

                    PM = PModule.PM_telecom(
                        inputs,
                        zone,
                        line
                    )

                if PM > 0:
                    PM_values.append(PM)

            if len(services) == 1:

                PM_total = max(PM_values) if PM_values else 0

            else:

                PM_combined = 1

                for pm in PM_values:
                    PM_combined *= (1 - pm)

                PM_total = 1 - PM_combined

            RM1E = (
                NM
                * PM_total
                * PPE
                * Pe
                * LO1E
            )

            RM2E = (
                NM
                * PM_total
                * Pe
                * LO2E
            )

            # =========================
            # S3 — RV and RW per line
            # =========================

            RV1E_values = []
            RV2E_values = []

            RW1E_values = []
            RW2E_values = []

            for line in inputs.lines:

                PV = PModule.PV(
                    inputs,
                    zone,
                    line
                )

                PW = PModule.PW(
                    inputs,
                    zone,
                    line
                )

                RV1E_line = (
                    (line.NL + NDJ)
                    * PV
                    * PPE
                    * LF1E
                )

                RV2E_line = (
                    (line.NL + NDJ)
                    * PV
                    * LF2E
                )

                RW1E_line = (
                    (line.NL + NDJ)
                    * PW
                    * PPE
                    * Pe
                    * LO1E
                )

                RW2E_line = (
                    (line.NL + NDJ)
                    * PW
                    * Pe
                    * LO2E
                )

                RV1E_values.append(RV1E_line)
                RV2E_values.append(RV2E_line)

                RW1E_values.append(RW1E_line)
                RW2E_values.append(RW2E_line)

            RV1E = sum(RV1E_values)
            RV2E = sum(RV2E_values)

            RW1E = sum(RW1E_values)
            RW2E = sum(RW2E_values)

            # =========================
            # S4 — RZ per line
            # =========================

            RZ1E_values = []
            RZ2E_values = []

            for line in inputs.lines:

                PZ = PModule.PZ(
                    inputs,
                    zone,
                    line
                )

                RZ1E_line = (
                    line.NI
                    * PZ
                    * PPE
                    * Pe
                    * LO1E
                )

                RZ2E_line = (
                    line.NI
                    * PZ
                    * Pe
                    * LO2E
                )

                RZ1E_values.append(RZ1E_line)
                RZ2E_values.append(RZ2E_line)

            RZ1E = sum(RZ1E_values)
            RZ2E = sum(RZ2E_values)

            # =========================
            # ANNEX E TOTALS
            # =========================

            RE1 = (
                RB1E
                + RC1E
                + RM1E
                + RV1E
                + RW1E
                + RZ1E
            )

            RE2 = (
                RB2E
                + RC2E
                + RM2E
                + RV2E
                + RW2E
                + RZ2E
            )

            RE_total = RE1 + RE2

            annex_E_results[zone.name] = {

                "PPE": PPE,

                "LF1E": LF1E,
                "LF2E": LF2E,
                "LO1E": LO1E,
                "LO2E": LO2E,

                "RB1E": RB1E,
                "RB2E": RB2E,

                "RC1E": RC1E,
                "RC2E": RC2E,

                "RM1E": RM1E,
                "RM2E": RM2E,

                "RV1E": RV1E,
                "RV2E": RV2E,

                "RW1E": RW1E,
                "RW2E": RW2E,

                "RZ1E": RZ1E,
                "RZ2E": RZ2E,

                "RE1": RE1,
                "RE2": RE2,
                "RE_total": RE_total
            }

        return annex_E_results