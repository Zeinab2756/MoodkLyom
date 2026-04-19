from typing import List
from pydantic import BaseModel

# just for reference
class EmotionRequest(BaseModel):
    text: str

class EmotionAlternative(BaseModel):
    emotion: str
    probability: float

class EmotionResponse(BaseModel):
    primary_emotion: str
    confidence: float
    alternative_emotions: List[EmotionAlternative]
