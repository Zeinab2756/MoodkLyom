package com.moodaklyom.data.model

data class TaskCreate(
    val title: String,
    val description: String? = null,
    val priority: String = "MEDIUM", // LOW, MEDIUM, HIGH, URGENT
    val deadline: String? = null // ISO format
)

data class TaskUpdate(
    val title: String? = null,
    val description: String? = null,
    val priority: String? = null,
    val deadline: String? = null,
    val is_completed: Boolean? = null
)

data class TaskResponse(
    val id: Int,
    val user_id: String,
    val title: String,
    val description: String? = null,
    val priority: String,
    val deadline: String? = null,
    val is_completed: Boolean,
    val created_at: String,
    val updated_at: String
)

data class TaskListResponse(
    val success: Boolean,
    val data: List<TaskResponse>,
    val total: Int,
    val completed: Int,
    val pending: Int
)

data class TaskSingleResponse(
    val success: Boolean,
    val data: TaskResponse
)

data class TaskStatsResponse(
    val success: Boolean,
    val data: TaskStats
)

data class TaskStats(
    val total: Int,
    val completed: Int,
    val pending: Int,
    val overdue: Int,
    val by_priority: Map<String, Int>
)

