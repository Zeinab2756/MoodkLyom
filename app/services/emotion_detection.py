"""
Emotion Detection Service
Interface for calling the teammate's AI model to detect emotions from text.
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration for emotion detection API
EMOTION_API_URL = os.getenv("EMOTION_API_URL", "http://0.0.0.0:8000/emotion/emotion/analyze")
EMOTION_API_TIMEOUT = int(os.getenv("EMOTION_API_TIMEOUT", "30"))


async def detect_emotions_from_text(text: str) -> Dict[str, Any]:
    """
    Send text to the emotion detection AI model and return detected emotions.
    
    Args:
        text: The transcribed text from the voice recording
        
    Returns:
        Dictionary containing emotion detection results
        Expected format: {
            "emotion": "happy",  # Primary emotion detected
            "emotion_level": 8,  # Emotion intensity level (1-10)
            "mood_level": 4,  # Converted to 1-5 scale for mood entries
            "confidence": 1.0,  # Confidence (derived from emotion_level)
            "tags": ["happy"],  # Tags based on emotion
            "emotions": ["happy"]  # List format for compatibility
        }
        
    Raises:
        Exception: If the API call fails
    """
    try:
        # Option 1: HTTP API call (if the model is served as an API)
        if EMOTION_API_URL.startswith("http"):
            try:
                import httpx
            except ImportError:
                # Fallback to requests if httpx not available
                try:
                    import requests
                    response = requests.post(
                        EMOTION_API_URL,
                        json={"text": text},
                        timeout=EMOTION_API_TIMEOUT
                    )
                    response.raise_for_status()
                    return format_emotion_result(response.json())
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # If API is not available, fall back to simple emotion detection
                    print(f"WARNING: Emotion API at {EMOTION_API_URL} is not available ({type(e).__name__}). Using fallback emotion detection.")
                    return _fallback_emotion_detection(text)
                except Exception as e:
                    # For other request errors, try fallback
                    error_msg = str(e)
                    if any(keyword in error_msg.lower() for keyword in ["connect", "connection", "timeout", "refused", "unreachable"]):
                        print(f"WARNING: Emotion API at {EMOTION_API_URL} is not available. Using fallback emotion detection.")
                        return _fallback_emotion_detection(text)
                    raise
            
            # Use async httpx for better performance
            try:
                async with httpx.AsyncClient(timeout=EMOTION_API_TIMEOUT) as client:
                    response = await client.post(
                        EMOTION_API_URL,
                        json={"text": text}
                    )
                    response.raise_for_status()
                    return format_emotion_result(response.json())
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                # If API is not available, fall back to simple emotion detection
                print(f"WARNING: Emotion API at {EMOTION_API_URL} is not available ({type(e).__name__}). Using fallback emotion detection.")
                return _fallback_emotion_detection(text)
            except Exception as e:
                # For other httpx errors, check if it's connection-related
                error_msg = str(e)
                if any(keyword in error_msg.lower() for keyword in ["connect", "connection", "timeout", "refused", "unreachable"]):
                    print(f"WARNING: Emotion API at {EMOTION_API_URL} is not available. Using fallback emotion detection.")
                    return _fallback_emotion_detection(text)
                raise
        
        # Option 2: Local file-based model (if the model is a local file)
        # This is a placeholder - you'll need to implement based on your teammate's model format
        # For example, if it's a pickle file, TensorFlow model, etc.
        else:
            # TODO: Implement local model loading and prediction
            # Example structure:
            # model = load_model(EMOTION_API_URL)  # or load from file path
            # result = model.predict(text)
            # return format_emotion_result(result)
            raise NotImplementedError(
                "Local model loading not yet implemented. "
                "Please set EMOTION_API_URL to an HTTP endpoint or implement local model loading."
            )
            
    except Exception as e:
        # Handle both httpx and requests exceptions
        error_msg = str(e)
        # If connection fails, use fallback emotion detection
        if "connect" in error_msg.lower() or "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print(f"WARNING: Emotion API at {EMOTION_API_URL} is not available. Using fallback emotion detection.")
            return _fallback_emotion_detection(text)
        if "httpx" in error_msg.lower() or "request" in error_msg.lower():
            raise Exception(f"Failed to call emotion detection API: {error_msg}")
        raise Exception(f"Error in emotion detection: {error_msg}")


def format_emotion_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the raw emotion detection result into a standardized format.
    
    Expected input format from teammate's AI model:
    {
        "emotion": "happy",  # Emotion name/title
        "emotion_level": 8   # Emotion intensity level (1-10)
    }
    
    Returns standardized format:
    {
        "emotion": "happy",
        "emotion_level": 8,  # 1-10 scale (original from AI model)
        "emotions": ["happy"],  # List format for compatibility
        "mood_level": 4,  # Converted to 1-5 scale for mood entries
        "confidence": 0.8,  # Derived from emotion_level (emotion_level / 10)
        "tags": ["happy"]
    }
    """
    # Handle the new format: emotion + emotion_level (1-10)
    if isinstance(raw_result, dict):
        emotion = raw_result.get("emotion") or raw_result.get("emotion_title") or raw_result.get("title")
        emotion_level = raw_result.get("emotion_level") or raw_result.get("level") or raw_result.get("emotionLevel")
        
        # If we have both emotion and emotion_level, use the new format
        if emotion and emotion_level is not None:
            try:
                emotion_level = int(emotion_level)
                # Ensure emotion_level is within valid range (1-10)
                emotion_level = max(1, min(10, emotion_level))
                
                # Convert emotion_level (1-10) to mood_level (1-5)
                mood_level = _convert_emotion_level_to_mood_level(emotion_level)
                
                # Calculate confidence from emotion_level (normalize to 0-1)
                confidence = emotion_level / 10.0
                
                return {
                    "emotion": emotion,
                    "emotion_level": emotion_level,
                    "emotions": [emotion],  # List format for compatibility
                    "mood_level": mood_level,
                    "confidence": confidence,
                    "tags": [emotion],
                    "raw_result": raw_result
                }
            except (ValueError, TypeError):
                pass  # Fall through to backward compatibility handling
        
        # Backward compatibility: Handle old probability-based formats
        # Check if it's a nested structure with probabilities
        if "emotions" in raw_result and isinstance(raw_result["emotions"], dict):
            emotion_probs = raw_result["emotions"]
            return _format_probability_based_result(emotion_probs, raw_result)
        # Check if keys are emotion names (strings) and values are probabilities
        elif all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in raw_result.items()):
            return _format_probability_based_result(raw_result, raw_result)
        # Check if it's already in the expected format
        elif "emotions" in raw_result and isinstance(raw_result["emotions"], list):
            return {
                "emotion": raw_result.get("emotion", ""),
                "emotion_level": raw_result.get("emotion_level", 5),
                "emotions": raw_result.get("emotions", []),
                "mood_level": raw_result.get("mood_level", 3),
                "confidence": raw_result.get("confidence", 0.0),
                "tags": raw_result.get("tags", []),
                "raw_result": raw_result
            }
    
    elif isinstance(raw_result, list):
        # Handle list format: [{"emotion": "happy", "probability": 0.85}, ...]
        emotion_probs = {}
        for item in raw_result:
            if isinstance(item, dict):
                emotion = item.get("emotion") or item.get("title") or item.get("name")
                prob = item.get("probability") or item.get("prob") or item.get("score")
                if emotion and prob is not None:
                    emotion_probs[emotion] = float(prob)
        if emotion_probs:
            return _format_probability_based_result(emotion_probs, raw_result)
    
    # Default fallback if format is not recognized
    return {
        "emotion": "neutral",
        "emotion_level": 5,
        "emotions": ["neutral"],
        "mood_level": 3,
        "confidence": 0.5,
        "tags": ["neutral"],
        "raw_result": raw_result
    }


def _format_probability_based_result(emotion_probs: Dict[str, float], raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to format probability-based emotion results (backward compatibility)."""
    if not emotion_probs:
        return {
            "emotion": "neutral",
            "emotion_level": 5,
            "emotions": [],
            "mood_level": 3,
            "confidence": 0.0,
            "tags": [],
            "raw_result": raw_result
        }
    
    # Sort emotions by probability (highest first)
    sorted_emotions = sorted(emotion_probs.items(), key=lambda x: x[1], reverse=True)
    
    # Get top emotion
    top_emotion = sorted_emotions[0][0] if sorted_emotions else "neutral"
    highest_prob = sorted_emotions[0][1] if sorted_emotions else 0.0
    
    # Convert probability to emotion_level (1-10)
    emotion_level = int(round(highest_prob * 10))
    emotion_level = max(1, min(10, emotion_level))
    
    # Convert to mood_level (1-5)
    mood_level = _convert_emotion_level_to_mood_level(emotion_level)
    
    # Get top emotions (above 0.1 threshold or top 3)
    threshold = 0.1
    top_emotions = [emotion for emotion, prob in sorted_emotions if prob >= threshold]
    if not top_emotions:
        top_emotions = [emotion for emotion, prob in sorted_emotions[:3]]
    
    return {
        "emotion": top_emotion,
        "emotion_level": emotion_level,
        "emotions": top_emotions,
        "mood_level": mood_level,
        "confidence": float(highest_prob),
        "tags": top_emotions,
        "raw_result": raw_result
    }


def _fallback_emotion_detection(text: str) -> Dict[str, Any]:
    """
    Simple fallback emotion detection when the API is not available.
    Uses keyword matching to detect basic emotions.
    
    Returns emotion and emotion_level (1-10) based on text content.
    """
    text_lower = text.lower()
    
    # Define emotion keywords and their intensity
    emotion_keywords = {
        "happy": ["happy", "joy", "joyful", "glad", "cheerful", "excited", "great", "wonderful", "amazing", "love", "good", "sunny", "nice"],
        "sad": ["sad", "depressed", "down", "unhappy", "miserable", "terrible", "awful", "bad", "horrible"],
        "angry": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated"],
        "anxious": ["anxious", "worried", "nervous", "stressed", "scared", "afraid", "fear"],
        "calm": ["calm", "peaceful", "relaxed", "content", "serene", "tranquil"],
        "neutral": ["okay", "fine", "alright", "normal", "neutral"]
    }
    
    # Count matches for each emotion
    emotion_scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    # Determine primary emotion
    if emotion_scores:
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[primary_emotion]
        
        # Convert score to emotion_level (1-10)
        # More keywords matched = higher intensity
        if max_score >= 3:
            emotion_level = 8  # High intensity
        elif max_score >= 2:
            emotion_level = 6  # Medium-high intensity
        else:
            emotion_level = 5  # Medium intensity
        
        # Adjust based on emotion type
        if primary_emotion in ["happy", "calm"]:
            emotion_level = min(10, emotion_level + 1)  # Boost positive emotions
        elif primary_emotion in ["sad", "angry", "anxious"]:
            emotion_level = max(1, emotion_level - 1)  # Lower negative emotions slightly
    else:
        # No emotion keywords found, default to neutral
        primary_emotion = "neutral"
        emotion_level = 5
    
    return {
        "emotion": primary_emotion,
        "emotion_level": emotion_level,
        "emotions": [primary_emotion],
        "mood_level": _convert_emotion_level_to_mood_level(emotion_level),
        "confidence": emotion_level / 10.0,
        "tags": [primary_emotion],
        "raw_result": {"emotion": primary_emotion, "emotion_level": emotion_level}
    }


def _convert_emotion_level_to_mood_level(emotion_level: int) -> int:
    """
    Convert emotion level (1-10 scale) to mood level (1-5 scale).
    
    Mapping:
    - 1-2 (very low) -> 1 (very bad)
    - 3-4 (low) -> 2 (bad)
    - 5-6 (medium) -> 3 (neutral)
    - 7-8 (high) -> 4 (good)
    - 9-10 (very high) -> 5 (excellent)
    """
    if emotion_level <= 2:
        return 1
    elif emotion_level <= 4:
        return 2
    elif emotion_level <= 6:
        return 3
    elif emotion_level <= 8:
        return 4
    else:  # 9-10
        return 5


def _map_emotions_to_mood_level(emotion_probs: Dict[str, float], sorted_emotions: list) -> int:
    """
    Map detected emotions to a mood level (1-5 scale) based on emotion categories.
    This is used for backward compatibility with probability-based formats.
    
    Positive emotions (happy, joyful, excited, content, calm) -> 4-5
    Neutral emotions (neutral, calm, content) -> 3
    Negative emotions (sad, angry, anxious, stressed, frustrated) -> 1-2
    """
    # Define emotion categories
    positive_emotions = {
        "happy", "joyful", "excited", "elated", "content", "peaceful", 
        "calm", "grateful", "optimistic", "hopeful", "cheerful", "enthusiastic"
    }
    negative_emotions = {
        "sad", "angry", "anxious", "stressed", "frustrated", "depressed",
        "worried", "fearful", "upset", "disappointed", "lonely", "tired"
    }
    neutral_emotions = {
        "neutral", "indifferent", "bored", "confused"
    }
    
    # Calculate weighted mood score
    positive_score = 0.0
    negative_score = 0.0
    neutral_score = 0.0
    
    for emotion, probability in emotion_probs.items():
        emotion_lower = emotion.lower()
        if emotion_lower in positive_emotions:
            positive_score += probability
        elif emotion_lower in negative_emotions:
            negative_score += probability
        elif emotion_lower in neutral_emotions:
            neutral_score += probability
    
    # Determine mood level based on dominant emotion category
    if positive_score > negative_score and positive_score > neutral_score:
        # Positive emotions dominate
        if positive_score >= 0.7:
            return 5  # Very positive
        elif positive_score >= 0.4:
            return 4  # Positive
        else:
            return 3  # Slightly positive
    elif negative_score > positive_score and negative_score > neutral_score:
        # Negative emotions dominate
        if negative_score >= 0.7:
            return 1  # Very negative
        elif negative_score >= 0.4:
            return 2  # Negative
        else:
            return 3  # Slightly negative
    else:
        # Neutral or balanced
        return 3

