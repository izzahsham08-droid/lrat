

from models.building import BuildingInput
from models.line import Line
from models.zone import Zone
from modules.p_module import PModule


def build_building_from_session(
    building_data,
    lines_data,
    zones_data
):

    building = BuildingInput()

    # ------------------------------
    # Building data
    # ------------------------------
    for key, value in building_data.items():
        setattr(building, key, value)
    # ------------------------------
    # Lines
    # ------------------------------
    building.lines = []

    for line_data in lines_data:

        line = Line()

        line.has_line_sections = line_data.get(
            "has_line_sections",
            False
        )
        line.sections = line_data.get(
            "sections",
            []
        )

        for key, value in line_data.items():
            setattr(line, key, value)

        building.lines.append(line)

    # ------------------------------
    # Zones
    # ------------------------------
    building.zones = []

    for zone_data in zones_data:

        zone = Zone(zone_data["name"])

        for key, value in zone_data.items():

            if key != "name":
                setattr(zone, key, value)

        zone.Pp = PModule.calculate_Pp(
            building,
            zone
        )

        zone.Pe = PModule.calculate_Pe(
            zone
        )

        building.zones.append(zone)

    return building