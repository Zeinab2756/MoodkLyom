package com.moodaklyom.data.model

data class MoodCreate(
    val date: String, // YYYY-MM-DD
    val moodLevel: Int, // 1-5
    val emoji: String? = null,
    val emotion: String? = null,
    val tags: List<String>? = null,
    val notes: String? = null
)

data class MoodResponse(
    val id: Int,
    val userId: String,
    val date: String,
    val moodLevel: Int,
    val emoji: String? = null,
    val emotion: String? = null,
    val tags: List<String>? = null,
    val notes: String? = null
)

data class MoodSummary(
    val total: Int,
    val average: Float,
    val byDay: List<MoodDay>,
    val topTags: List<String>,
    val trend: String
)

data class MoodDay(
    val date: String,
    val mood: Int
)

data class MoodListResponse(
    val moods: List<MoodResponse>,
    val total: Int,
    val limit: Int,
    val offset: Int
)

