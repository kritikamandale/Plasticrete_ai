"""
Tell the user which use-class failed. Do not invent a strength or carbon delta.
"""
from dataclasses import dataclass


@dataclass
class RemediationResult:
    top_negative_factor:  str
    remediation_action_1: str
    remediation_action_2: str
    remediation_action_3: str
    estimated_score_gain: float


class RemediationAdvisor:
    def advise(self, gates: list[dict], balance: dict) -> RemediationResult:
        refused = [gate for gate in gates if gate.get("status") == "refused"]
        crossing = [gate for gate in gates if gate.get("status") == "verification_batch"]
        plastic = balance.get("plastic_kg_m3")
        carbon = balance.get("co2_kgco2e_m3")
        if refused:
            names = ", ".join(gate.get("label", gate.get("id", "use")) for gate in refused)
            return RemediationResult(
                top_negative_factor=str(refused[0].get("id", "use_class")),
                remediation_action_1=f"{names} did not clear on the conservative side of the 90% interval.",
                remediation_action_2="Change the recipe and run the model again. This note does not add megapascals by hand.",
                remediation_action_3="The mass balance for this recipe is the carbon and plastic number to keep.",
                estimated_score_gain=0.0,
            )
        if crossing:
            names = ", ".join(gate.get("label", gate.get("id", "use")) for gate in crossing)
            return RemediationResult(
                top_negative_factor=str(crossing[0].get("id", "use_class")),
                remediation_action_1=f"{names}: cast one verification batch. The interval crosses the grade line.",
                remediation_action_2=f"This recipe diverts {plastic} kg plastic per m³.",
                remediation_action_3=f"This recipe is {carbon} kg CO₂e per m³ on the shared factor table.",
                estimated_score_gain=0.0,
            )
        return RemediationResult(
            top_negative_factor="none",
            remediation_action_1="Every non-structural gate that was checked is allowed or a lab trial.",
            remediation_action_2=f"Plastic diverted: {plastic} kg/m³.",
            remediation_action_3=f"Embodied carbon: {carbon} kg CO₂e/m³.",
            estimated_score_gain=0.0,
        )
