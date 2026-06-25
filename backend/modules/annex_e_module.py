from mappings.mapping import Mapping

class AnnexEModule:


    @staticmethod
    def calculate_PPE(zone):

        if not zone.annex_E_applicable:
            return 0

        if not zone.annex_E_surrounding_types:
            return 1

        values = []

        for surrounding_type in zone.annex_E_surrounding_types:

            values.append(
                Mapping.ANNEX_E_PPE_MAPPING[
                    surrounding_type
                ]
            )

        return max(values)
    

    @staticmethod
    def calculate_LF1E(inputs, zone):

        if not zone.annex_E_applicable:
            return 0

        if not zone.fire_explosion_can_injure_surroundings:
            return 0

        values = Mapping.ANNEX_E_L1_MAPPING[
            zone.annex_E_scenario
        ][
            zone.annex_E_spread_area
        ]

        LF1E = values["LF1E"]

        if (
            inputs.TWS
            and
            zone.annex_E_spread_area
            == "inside_site_fence"
        ):
            LF1E *= (1 - inputs.PTWS)

        return LF1E
    
    @staticmethod
    def calculate_LO1E(inputs, zone):

        if not zone.annex_E_applicable:
            return 0

        if not zone.internal_failure_can_injure_surroundings:
            return 0

        values = Mapping.ANNEX_E_L1_MAPPING[
            zone.annex_E_scenario
        ][
            zone.annex_E_spread_area
        ]

        LO1E = values["LO1E"]

        if (
            inputs.TWS
            and
            zone.annex_E_spread_area
            == "inside_site_fence"
        ):
            LO1E *= (1 - inputs.PTWS)

        return LO1E
    

    @staticmethod
    def calculate_LF2E(zone):

        if not zone.annex_E_applicable:
            return 0

        if not zone.fire_explosion_can_damage_surroundings:
            return 0

        return Mapping.ANNEX_E_L2_MAPPING[
            zone.annex_E_scenario
        ]["LF2E"]
    
    @staticmethod
    def calculate_LO2E(zone):

        if not zone.annex_E_applicable:
            return 0

        if not zone.internal_failure_can_damage_surroundings:
            return 0

        return Mapping.ANNEX_E_L2_MAPPING[
            zone.annex_E_scenario
        ]["LO2E"] 
    