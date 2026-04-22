package com.moodaklyom.data.model

data class TranscriptionResponse(
    val success: Boolean,
    val transcribed_text: String?,
    val emotion: EmotionData? = null,
    val message: String? = null
)

data class EmotionData(
    val primary_emotion: String,
    val confidence: Double,
    val alternative_emotions: List<EmotionAlternative>? = null
)

data class EmotionAlternative(
    val emotion: String,
    val probability: Double
)
