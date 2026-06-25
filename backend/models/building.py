
class BuildingInput:

    def __init__(self):

        # Lightning density inputs (A.1)

        self.NSG = 4      # lightning ground strike-point density
        self.NG = None    # ground flash density
        self.NT = None    # total flashes (satellite data)

        self.k = 2        # correction factor (default)

        # Geometry
        self.L = 20
        self.W = 40
        self.H = 25

        self.adjacent_structure = False

        self.L_adj = 0
        self.W_adj = 0
        self.H_adj = 0

        self.CDJ = 1

    

        # Equipment parameter
        self.Uw_structure = 1.5

        # structure shape
        self.structure_shape = "rectangular"
        # options: "rectangular" or "complex"

        # complex structure parameters
        self.Hmin = None
        self.Hp = None
        
        #Cd
        # location type
        self.location_type = "isolated"
        # options:
        # "surrounded_high"
        # "surrounded_same"
        # "isolated"
        # "hilltop

        #self.people_present = True
        #self.internal_system_present = True

        # Internal system
        #self.Pe = 1.0

        # Lines
       # self.power_line_exists = True
       # self.telecom_line_exists = False

        self.line_length_known = True

        # ------------------------------
        # PLPS (Table B.3)
        # ------------------------------
        # Protection
        self.LPS_class = None     #table b.3
        #self.SPD_present = False
        self.TWS = False
        self.PTWS = None

        # Natural LPS conditions (Annex B Note 3)
        self.extensive_metal_framework = False
        self.reinforced_concrete_interconnected = False
 
        self.metal_roof = False
        self.complete_roof_protection = False

        # ------------------------------
        # PS (Table B.4)
        # ------------------------------
        #CONSTRUCTION TYPE (Ps input factor)
        self.wall_material = "reinforced_concrete"
        self.roof_material = "reinforced_concrete"
        self.reinforcement_interconnected = True
        self.unbonded_metal_parts = False

        # ------------------------------
        # Pam natural LPS condition
        # ------------------------------
        self.mesh_earth_termination = False
        self.accessible_metal_installation = True

        # Structure has electromagnetic shielding
        self.structure_shielding = False

        # Spatial shield width wm1 (m)
        # Used when shielding exists
        self.wm1 = None

        # Continuous metal electromagnetic shield
        # IEC special case (>= 0.1 mm assumed)
        self.continuous_metal_shield = False

        # Meshed bonding network
        self.meshed_bonding_network = False

        self.lines = []
        self.zones = []




