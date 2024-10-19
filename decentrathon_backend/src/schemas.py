from pydantic import BaseModel


class EvaluationRequest(BaseModel):
    prompt: str
    pupil_text: str
    