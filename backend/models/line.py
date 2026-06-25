class LineSection:

    def __init__(self):

        self.name = ""

        # Section length
        self.LL = 0.0

        # Annex A section parameters
        self.installation = "buried"
        self.type = "lv_telecom_data_hv_with_transformer"
        self.environmental = "suburban"

        # Section shielding / screen resistance
        self.shielded = False
        self.shield_resistance = "unshielded"

class Line:

    def __init__(self):

        # ------------------------------
        # Basic line information
        # ------------------------------

        # "power" or "telecom"
        self.name = ""
        self.service = "power"

        # ------------------------------
        # Annex A parameters
        # ------------------------------

        # Table A.2 — CI
        # "aerial"
        # "buried"
        # "buried_mesh"
        self.installation = "buried"

        # Table A.3 — CT
        # "lv_or_telecom"
        # "hv_transformer_separated"
        self.type = "lv_telecom_data_hv_with_transformer"

        # Table A.4 — CE
        # "rural"
        # "suburban"
        # "urban"
        # "urban_dense"
        self.environmental = "suburban"

        # Line length (m)
        self.LL = 1000
        self.length_known = True   # if False, use IEC 1000 m default (Clause A.4)

        # Equipment impulse withstand voltage (kV)
        self.Uw = 1.5
        self.has_line_sections = False
        self.sections = []

        # Adjacent structure at the FAR END of this line (Annex A Eq A.6, Annex F Table F.2/F.3)
        # NDJ = NSG x ADJ x CDJ x CT x 1e-6 ; computed per line.
        self.adjacent_structure = False
        self.L_adj = 0
        self.W_adj = 0
        self.H_adj = 0
        self.CDJ = 1
        self.NDJ = 0   # computed value, stored per line

        # ------------------------------
        # Future sectioning support
        # ------------------------------

        # IEC 8.4 — line section identifier
        #self.section_id = None

        # ------------------------------
        # SPD protection
        # ------------------------------

        # SPD level for THIS line
        # "none"
        # "III_IV"
        # "II"
        # "I"
        # "better_2_5"
        # "better_3_75"
        # "better_5"
        #self.spd_level = "none"
        #self.use_custom_pspd = False

        #self.custom_pspd = None

        # ------------------------------
        # CLD / CLI shared conditions
        # IEC Table B.9
        # ------------------------------

        # External conductive line exists
        self.has_external_line = True

        # Lightning protective routing
        # (metallic conduit, duct, protected routing)
        self.lightning_protective_routing = False

        # Shielded external line
        self.shielded = False

        # Shield bonded to same bonding bar
        # as equipment
        self.same_bonding_bar = False

        # Multi grounded neutral power line
        self.multi_grounded_neutral = False

        # Protected/tested isolating interface
        self.isolating_interface_protected = False

        # ------------------------------
        # Future KS / LPZ logic
        # ------------------------------

        self.routing_precaution = False

        self.same_bonding_bar = False

        self.mesh_bonding_network = False

        # ------------------------------
        # Future PLD logic
        # ------------------------------

        self.equipotential_bonding_spd = False
        self.equipotential_bonding_level = "none"
        #"none"
        #"III-IV"
        #"II"
        #"I"
        # ------------------------------
        # Future internal system link
        # ------------------------------

        self.shield_resistance = None
        self.external_cable = "metallic"