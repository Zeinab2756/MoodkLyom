package com.moodaklyom.data.model

data class User(
    val id: String,
    val username: String,
    val avatar: String? = null,
    val preferences: Map<String, Any> = emptyMap(),
    val createdAt: String? = null
)

