from .tools import build_fhir
from .abdm_client import ABDMClient

class OutputAgent:
    def __init__(self):
        self.abdm = ABDMClient()

    def run(self, state, patient_ref, auto_push=False):
        try:
            fhir = build_fhir(state, patient_ref)
        except Exception as e:
            print(f"FHIR build error: {str(e)}")
            fhir = None

        result = {
            "fhir": fhir,
            "pushed": False,
            "push_response": None
        }

        if auto_push and not state.get("needs_human_review", True) and fhir:
            try:
                resp = self.abdm.push_condition(fhir)
                result["pushed"] = True
                result["push_response"] = resp
            except Exception as e:
                print(f"ABDM push error: {str(e)}")
                result["push_response"] = {"error": str(e)}

        return result
