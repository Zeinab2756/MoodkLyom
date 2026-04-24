package com.moodaklyom.data.model

data class HackCreate(
    val title: String,
    val content: String,
    val category: String? = null,
    val tags: List<String>? = null
)

data class HackUpdate(
    val title: String? = null,
    val content: String? = null,
    val category: String? = null,
    val tags: List<String>? = null
)

data class HackResponse(
    val id: Int,
    val title: String,
    val content: String,
    val category: String? = null,
    val tags: List<String>? = null,
    val created_at: String,
    val updated_at: String
)

data class HackListResponse(
    val success: Boolean,
    val data: List<HackResponse>,
    val total: Int,
    val limit: Int,
    val offset: Int
)

data class HackSingleResponse(
    val success: Boolean,
    val data: HackResponse
)

data class WellnessTip(
    val id: Int,
    val title: String,
    val description: String,
    val category: String? = null,
    val tags: List<String>? = null
)

