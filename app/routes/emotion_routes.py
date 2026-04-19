from fastapi import APIRouter, HTTPException
from app.models.emotion_model import emotion_classifier
from app.schemas.emotion_schemas import EmotionRequest, EmotionResponse

router = APIRouter(prefix="/emotion", tags=["emotion"])


@router.post("/analyze", response_model=EmotionResponse)
async def analyze_emotion(request: EmotionRequest):
    """
    Analyze emotion from user text using fine-tuned BERT.
    """
    try:
        result = emotion_classifier.predict_emotion(request.text)

        # result already has the right keys:
        # primary_emotion, confidence, alternative_emotions
        return EmotionResponse(
            primary_emotion=result["primary_emotion"],
            confidence=result["confidence"],
            alternative_emotions=result["alternative_emotions"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing emotion: {str(e)}",
        )


@router.get("/health")
async def emotion_health_check():
    """
    Simple health check: run a test prediction and return it.
    """
    test_text = "I am very happy today!"
    result = emotion_classifier.predict_emotion(test_text)
    return {
        "status": "ok",
        "sample_text": test_text,
        "prediction": result,
    }
