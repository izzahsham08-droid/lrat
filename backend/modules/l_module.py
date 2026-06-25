from mappings.mapping import Mapping


class LModule:
    """
    Loss module.
    Per lecturer's instruction + IEC recommendation:
    each applicable loss component automatically uses the MAXIMUM (upper)
    value of its range from Table C.2. The user no longer selects upper/lower.
    """

    @staticmethod
    def _max_value(category_values, zone=None):
        """
        Return the highest value available in a category's loss range.
        Handles the special 'upper_note_e' key (normal/low LO1/LO2),
        which is only valid when Note e conditions are met.
        """
        # If an upper_note_e value exists, it is the maximum — but only
        # applicable when the Note e condition is satisfied.
        if "upper_note_e" in category_values:
            note_e_condition = bool(
                zone is not None and (
                    getattr(zone, "internal_system_hazard", False)
                    or getattr(zone, "environmental_hazard", False)
                    or getattr(zone, "pv_dc_fire_risk", False)
                )
            )
            if note_e_condition:
                return category_values["upper_note_e"]
            # Note e not met -> fall back to the lower value
            return category_values.get("lower", 0)

        # Normal case: just take the largest numeric value in the range
        return max(category_values.values())

    @staticmethod
    def calculate_LT(zone):
        if not zone.LT_applicable:
            return 0
        return 1e-2

    @staticmethod
    def calculate_LD(zone):
        if not zone.LD_applicable:
            return 0
        allowed = Mapping.LD_ALLOWED_VALUES
        # Use the maximum allowed LD value as default
        return max(allowed.values())

    @staticmethod
    def calculate_LF1(zone):
        if not zone.LF1_applicable:
            return 0
        if zone.loss_category not in Mapping.LOSS_MAPPING:
            raise ValueError("Invalid loss category")
        category_values = Mapping.LOSS_MAPPING[zone.loss_category]["LF1"]
        return LModule._max_value(category_values, zone)

    @staticmethod
    def calculate_LF2(zone):
        if not zone.LF2_applicable:
            return 0
        if zone.loss_category not in Mapping.LOSS_MAPPING:
            raise ValueError("Invalid loss category")
        category_values = Mapping.LOSS_MAPPING[zone.loss_category]["LF2"]
        return LModule._max_value(category_values, zone)

    @staticmethod
    def calculate_LO1(zone):
        if not zone.LO1_applicable:
            return 0
        if zone.loss_category not in Mapping.LOSS_MAPPING:
            raise ValueError("Invalid loss category")
        category_values = Mapping.LOSS_MAPPING[zone.loss_category]["LO1"]
        return LModule._max_value(category_values, zone)

    @staticmethod
    def calculate_LO2(zone):
        if not zone.LO2_applicable:
            return 0
        if zone.loss_category not in Mapping.LOSS_MAPPING:
            raise ValueError("Invalid loss category")
        category_values = Mapping.LOSS_MAPPING[zone.loss_category]["LO2"]
        return LModule._max_value(category_values, zone)
