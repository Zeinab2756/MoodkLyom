package com.moodaklyom.data.model

data class TranscriptionResponse(
    val success: Boolean,
    val transcribed_text: String?,
    val emotion: EmotionResult?,
    val pcm_path: String?
)

data class EmotionResult(
    val primary_emotion: String?,
    val confidence: Float?,
    val alternative_emotions: List<AlternativeEmotion>?
)

data class AlternativeEmotion(
    val label: String,
    val score: Float
)
