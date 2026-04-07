package com.moodaklyom.data.model

data class FullAnalysisResponse(
    val success: Boolean,
    val text: String,
    val emotion: String,
    val confidence: Double,
    val alternatives: List<EmotionAlt>? = null
)

data class EmotionAlt(
    val emotion: String,
    val probability: Double
)
