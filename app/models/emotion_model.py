# app/models/emotion_model.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class EmotionClassifier:
    def __init__(self):
        # Use a pre-trained emotion classification model from Hugging Face
        self.model_name = "bhadresh-savani/bert-base-uncased-emotion"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.eval()  # set to evaluation mode

        # Load the emotion labels
        self.emotions = self.model.config.id2label

        print("✅ Hugging Face BERT emotion model loaded successfully!")

    def predict_emotion(self, text: str):
        """Predict emotion from text using Hugging Face BERT model"""
        if not text:
            return {"primary_emotion": None, "confidence": 0.0, "alternative_emotions": []}

        # Tokenize input
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        
        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=1).squeeze().cpu().numpy()

        # Top 3 predictions
        top3_idx = probs.argsort()[-3:][::-1]
        top3_emotions = [self.emotions[i] for i in top3_idx]
        top3_probs = [float(probs[i]) for i in top3_idx]

        return {
            "primary_emotion": top3_emotions[0],
            "confidence": top3_probs[0],
            "alternative_emotions": [
                {"emotion": emo, "probability": prob}
                for emo, prob in zip(top3_emotions, top3_probs)
            ],
        }


# Create a singleton instance
emotion_classifier = EmotionClassifier()
