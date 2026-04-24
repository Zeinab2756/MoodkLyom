package com.moodaklyom.data.model

data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: ApiError? = null
)

data class ApiError(
    val code: String,
    val message: String,
    val details: Map<String, Any>? = null
)

data class LoginData(
    val user: User,
    val token: String
)

