import math
from mappings.mapping import Mapping

class LightningDensity:

    @staticmethod
    def calculate_NSG(inputs):

        if inputs.NSG is not None:
            return inputs.NSG

        elif inputs.NG is not None:
            return inputs.k * inputs.NG

        elif inputs.NT is not None:
            return 0.5 * inputs.NT

        else:
            raise ValueError("No lightning density data provided")
        


class NModule:

    @staticmethod
    def AD_rectangular(inputs):

        L = inputs.L
        W = inputs.W
        H = inputs.H

        AD = (L * W) + (2 * (3 * H) * (L + W)) + (math.pi * (3 * H) ** 2)

        return AD
    
    @staticmethod
    def AD_complex(inputs):

        L = inputs.L
        W = inputs.W

        Hmin = inputs.Hmin
        Hp = inputs.Hp

        ADmin = (L * W) + (2 * (3 * Hmin) * (L + W)) + (math.pi * (3 * Hmin) ** 2)

        ADp = math.pi * (3 * Hp) ** 2

        return max(ADmin, ADp)
    
    @staticmethod
    def AD(inputs):

        if inputs.structure_shape == "rectangular":

            return NModule.AD_rectangular(inputs)

        elif inputs.structure_shape == "complex":

            return NModule.AD_complex(inputs)

        else:

            raise ValueError("Unknown structure shape")
        
    

    @staticmethod
    def CD(inputs):

        return Mapping.CD[inputs.location_type]

    @staticmethod
    def ND(inputs):
        

        NSG = LightningDensity.calculate_NSG(inputs)

        AD = NModule.AD(inputs)

        CD = NModule.CD(inputs)

        ND = NSG * AD * CD * 1e-6

        
        return ND
    
    @staticmethod
    def AM(inputs):

        L = inputs.L
        W = inputs.W
        Uw_values = [

            line.Uw

            for line in inputs.lines

            if line.Uw is not None
        ]

        Uw_structure = min(Uw_values)
        

        rM = 350 / Uw_structure

        AM = 2 * rM * (L + W) + math.pi * (rM ** 2)

        return AM


    @staticmethod
    def NM(inputs):

        AM = NModule.AM(inputs)

        NSG = LightningDensity.calculate_NSG(inputs)

        NM = (1 / inputs.k) * NSG * AM * 1e-6

        return NM
    
    @staticmethod
    def prepare_lines(inputs):

    # STEP 1 — apply unknown length assumption (per line)
    # Annex A Clause A.4: when section length is unknown, assume 1000 m.
        for line in inputs.lines:
            # Per-line flag; fall back to building-level flag for backward compatibility
            line_known = getattr(line, "length_known", None)
            if line_known is None:
                line_known = getattr(inputs, "line_length_known", True)

            if not line_known:
                if getattr(line, "has_line_sections", False) and getattr(line, "sections", []):
                    for s in line.sections:
                        if not s.get("LL"):
                            s["LL"] = 1000
                else:
                    if not line.LL:
                        line.LL = 1000

    # STEP 2 — compute total power length
        power_total = 0

        for line in inputs.lines:
            if line.service == "power":
                if getattr(line, "has_line_sections", False) and getattr(line, "sections", []):
                    # Sum section lengths
                    power_total += sum(s.get("LL", 0) or 0 for s in line.sections)
                else:
                    power_total += (line.LL or 0)

    # STEP 3 — enforce IEC realistic limit (2 km)
        if power_total > 2000:

            scale = 2000 / power_total

            for line in inputs.lines:
                if line.service == "power":
                    if getattr(line, "has_line_sections", False) and getattr(line, "sections", []):
                        for s in line.sections:
                            s["LL"] = (s.get("LL", 0) or 0) * scale
                    elif line.LL:
                        line.LL *= scale

    @staticmethod
    def AL(LL):

        AL = 40 * LL

        return AL


    @staticmethod
    def NL(inputs):

        NSG = LightningDensity.calculate_NSG(inputs)

        for i, line in enumerate(inputs.lines, start=1):

            if line.external_cable == "fibre_optic":
                line.NL = 0
                continue

            # If line is divided into sections
            if (
                getattr(line, "has_line_sections", False)
                and getattr(line, "sections", [])
            ):

                NL_total = 0

                for section in line.sections:

                    LL = section.get("LL", 0)
                    CI = Mapping.CI[section.get("installation")]
                    CE = Mapping.CE[section.get("environmental")]
                    CT = Mapping.CT[section.get("type")]

                    AL = NModule.AL(LL)

                    NL_section = NSG * AL * CI * CE * CT * 1e-6

                    NL_total += NL_section

                line.NL = NL_total

            # Existing single-section logic
            else:

                LL = line.LL
                CI = Mapping.CI[line.installation]
                CE = Mapping.CE[line.environmental]
                CT = Mapping.CT[line.type]

                AL = NModule.AL(LL)

                NL = NSG * AL * CI * CE * CT * 1e-6

                line.NL = NL


    
    
    @staticmethod
    def AI(LL, Uw):

        rI = 2000 / (Uw ** 1.8)

        AI = 2 * rI * LL

        return AI
    
    @staticmethod
    def NI(inputs):

        NSG = LightningDensity.calculate_NSG(inputs)

        k = inputs.k

        for i, line in enumerate(inputs.lines, start=1):

            if line.external_cable == "fibre_optic":
                line.NI = 0
                continue

            # If line is divided into sections
            if (
                getattr(line, "has_line_sections", False)
                and getattr(line, "sections", [])
            ):

                NI_total = 0

                for section in line.sections:

                    LL = section.get("LL", 0)
                    Uw = line.Uw

                    CI = Mapping.CI[section.get("installation")]
                    CE = Mapping.CE[section.get("environmental")]
                    CT = Mapping.CT[section.get("type")]

                    AI = NModule.AI(LL, Uw)

                    NI_section = (1 / k) * NSG * AI * CI * CE * CT * 1e-6

                    NI_total += NI_section

                line.NI = NI_total

            # Existing single-section logic
            else:

                LL = line.LL
                Uw = line.Uw

                CI = Mapping.CI[line.installation]
                CE = Mapping.CE[line.environmental]
                CT = Mapping.CT[line.type]

                AI = NModule.AI(LL, Uw)

                NI = (1 / k) * NSG * AI * CI * CE * CT * 1e-6

                line.NI = NI

                #print(f"Line {i}")
                #print("LL =", LL)
                #print("AI =", AI)
                #print("NI =", NI)
                #print()

          
    

    @staticmethod
    def NDJ_for_line(inputs, line):
        """
        NDJ for the adjacent structure connected at the FAR END of THIS line.
        Annex A Eq A.6: NDJ = NSG x ADJ x CDJ x CT x 1e-6
        Each line can have its own adjacent structure (Annex F Table F.2/F.3).
        """
        if not getattr(line, "adjacent_structure", False):
            return 0

        NSG = LightningDensity.calculate_NSG(inputs)

        L = line.L_adj
        W = line.W_adj
        H = line.H_adj

        # Collection area of the adjacent structure
        ADJ = (L * W) + (2 * (3 * H) * (L + W)) + (math.pi * (3 * H) ** 2)

        CDJ = line.CDJ
        CT = Mapping.CT.get(line.type, 1)

        NDJ = NSG * ADJ * CDJ * CT * 1e-6
        return NDJ

    @staticmethod
    def NDJ(inputs):
        """
        Backward-compatible: total NDJ summed across all lines.
        (Kept so existing callers don't break; per-line values are also
        stored on each line as line.NDJ.)
        """
        total = 0
        for line in inputs.lines:
            ndj = NModule.NDJ_for_line(inputs, line)
            line.NDJ = ndj
            total += ndj
        return total
