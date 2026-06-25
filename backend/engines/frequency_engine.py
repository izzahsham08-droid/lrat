from modules.n_module import NModule
from modules.p_module import PModule

class FrequencyEngine:

    @staticmethod
    def combine_by_service(probability_by_service):

        service_values = []

        for service, values in probability_by_service.items():

            # Same service = same internal system category
            # HV + LV power → use highest representative value
            service_value = max(values) if values else 0

            if service_value > 0:
                service_values.append(service_value)

        # Different services = different internal systems
        # power + telecom → IEC probability combination
        combined = 1

        for value in service_values:
            combined *= (1 - value)

        return 1 - combined


    @staticmethod
    def calculate_F(inputs):

        # Prepare line N values
        NModule.prepare_lines(inputs)
        NModule.NL(inputs)
        NModule.NI(inputs)

        ND = NModule.ND(inputs)
        NM = NModule.NM(inputs)
        NDJ = NModule.NDJ(inputs)

        results = {}
        building_total = 0

        for zone in inputs.zones:

            if not zone.internal_system_present:
                results[zone.name] = {
                    "FC": 0,
                    "FM": 0,
                    "FWP": 0,
                    "FWT": 0,
                    "FW": 0,

                    "FZP": 0,
                    "FZT": 0,
                    "FZ": 0,

                    "F_total": 0,
                    "FT": zone.FT,
                    "frequency_status": "Not applicable"
                }
                continue

            Pe = zone.Pe

            # =========================
            # FC = ND × PC × Pe
            # =========================
            PC_by_service = {}

            for line in inputs.lines:

                if line.service not in ["power", "telecom"]:
                    raise ValueError(
                        f"Unsupported service type: {line.service}"
                    )

                PC_line = PModule.PC(
                    inputs,
                    zone,
                    line
                )

                PC_by_service.setdefault(
                    line.service,
                    []
                ).append(PC_line)

            PC_total = FrequencyEngine.combine_by_service(
                PC_by_service
            )

            FC = ND * PC_total * Pe


            # =========================
            # FM = NM × PM × Pe
            # =========================
            PM_by_service = {}

            for line in inputs.lines:

                if line.service == "power":

                    PM_line = PModule.PM_power(
                        inputs,
                        zone,
                        line
                    )

                elif line.service == "telecom":

                    PM_line = PModule.PM_telecom(
                        inputs,
                        zone,
                        line
                    )

                else:
                    raise ValueError(
                        f"Unsupported service type: {line.service}"
                    )

                PM_by_service.setdefault(
                    line.service,
                    []
                ).append(PM_line)

            PM_total = FrequencyEngine.combine_by_service(
                PM_by_service
            )

            FM = NM * PM_total * Pe


            FWP = 0
            FWT = 0

            for line in inputs.lines:

                PW_line = PModule.PW(inputs, zone, line)

                FW_line = (
                    (line.NL + line.NDJ)
                    * PW_line
                    * Pe
                )

                if line.service == "power":
                    FWP += FW_line

                elif line.service == "telecom":
                    FWT += FW_line

                else:
                    raise ValueError(
                        f"Unsupported service type: {line.service}"
                    )

            FW = FWP + FWT


            # =========================
            # FZ = Σ[NI × PZ × Pe]
            # =========================
            FZP = 0
            FZT = 0

            for line in inputs.lines:

                PZ_line = PModule.PZ(inputs, zone, line)

                FZ_line = (
                    line.NI
                    * PZ_line
                    * Pe
                )

                if line.service == "power":
                    FZP += FZ_line

                elif line.service == "telecom":
                    FZT += FZ_line

                else:
                    raise ValueError(
                        f"Unsupported service type: {line.service}"
                    )

            FZ = FZP + FZT
               
            F_total = FC + FM + FW + FZ

            FT = zone.FT

            if F_total > FT:
                frequency_status = "Protection required"
            else:
                frequency_status = "Protection not required"

            results[zone.name] = {
                "Pe": Pe,
                "PC_by_service": PC_by_service,
                "PC_total": PC_total,
                "PM_by_service": PM_by_service,
                "PM_total": PM_total,
                "FC": FC,
                "FM": FM,

                "FWP": FWP,
                "FWT": FWT,
                "FW": FW,

                "FZP": FZP,
                "FZT": FZT,
                "FZ": FZ,
                "F_total": F_total,
                "FT": FT,
                "frequency_status": frequency_status
            }

        return results