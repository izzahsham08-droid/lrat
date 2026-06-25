class ComponentApplicability:

    @staticmethod
    def apply(zone):
        zone.RAT_applicable = (
            zone.LT_applicable
            and zone.people_present
        )

        zone.RAD_applicable = (
            zone.LD_applicable
            and zone.people_present
            and zone.people_exposed_on_structure
        )

        zone.RB_applicable = (
            zone.LF1_applicable
            or zone.LF2_applicable
        )

        zone.RC_applicable = (
            zone.internal_system_present
            and (zone.LO1_applicable or zone.LO2_applicable)
        )

        zone.RM_applicable = (
            zone.internal_system_present
            and (zone.LO1_applicable or zone.LO2_applicable)
        )

        zone.RU_applicable = (
            zone.internal_system_present
            and zone.LT_applicable
            and zone.people_present
        )

        zone.RV_applicable = (
            zone.internal_system_present
            and (zone.LF1_applicable or zone.LF2_applicable)
        )

        zone.RW_applicable = (
            zone.internal_system_present
            and (zone.LO1_applicable or zone.LO2_applicable)
        )

        zone.RZ_applicable = (
            zone.internal_system_present
            and (zone.LO1_applicable or zone.LO2_applicable)
        )

        return zone