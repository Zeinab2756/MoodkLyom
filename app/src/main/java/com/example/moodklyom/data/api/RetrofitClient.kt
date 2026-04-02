package com.moodaklyom.data.api

import com.moodaklyom.data.model.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*


interface ApiService {

    // User
    @POST("user/init")
    suspend fun loginOrSignup(
        @Body request: LoginRequest
    ): Response<ApiResponse<LoginData>>

    @GET("user/{id}")
    suspend fun getUser(@Path("id") id: String): Response<ApiResponse<User>>

    @PUT("user/update")
    suspend fun updateUser(@Body request: UpdateRequest): Response<ApiResponse<User>>

    // Mood
    @POST("mood/add")
    suspend fun addMood(@Body request: MoodCreate): Response<MoodResponse>

    @GET("mood/all")
    suspend fun getAllMoods(
        @Query("from") fromDate: String? = null,
        @Query("to") toDate: String? = null,
        @Query("limit") limit: Int = 100,
        @Query("offset") offset: Int = 0
    ): Response<MoodListResponse>

    @GET("mood/summary")
    suspend fun getMoodSummary(
        @Query("range") range: String? = null,
        @Query("from") fromDate: String? = null,
        @Query("to") toDate: String? = null
    ): Response<MoodSummary>

    @GET("mood/{date}")
    suspend fun getMoodByDate(@Path("date") date: String): Response<MoodResponse>

    // Tasks
    @POST("tasks/")
    suspend fun createTask(@Body request: TaskCreate): Response<TaskSingleResponse>

    @GET("tasks/")
    suspend fun getTasks(
        @Query("completed") completed: Boolean? = null,
        @Query("priority") priority: String? = null,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<TaskListResponse>

    @GET("tasks/{id}")
    suspend fun getTask(@Path("id") id: Int): Response<TaskSingleResponse>

    @PUT("tasks/{id}")
    suspend fun updateTask(
        @Path("id") id: Int,
        @Body request: TaskUpdate
    ): Response<TaskSingleResponse>

    @PATCH("tasks/{id}/toggle")
    suspend fun toggleTask(@Path("id") id: Int): Response<TaskSingleResponse>

    @DELETE("tasks/{id}")
    suspend fun deleteTask(@Path("id") id: Int): Response<ApiResponse<Map<String, String>>>

    @GET("tasks/stats/overview")
    suspend fun getTaskStats(): Response<TaskStatsResponse>

    // Hacks
    @POST("hacks/")
    suspend fun createHack(@Body request: HackCreate): Response<HackSingleResponse>

    @GET("resources/wellness")
    suspend fun getWellnessTips(): Response<List<WellnessTip>>

    @GET("hacks/{id}")
    suspend fun getHack(@Path("id") id: Int): Response<HackSingleResponse>

    @PUT("hacks/{id}")
    suspend fun updateHack(
        @Path("id") id: Int,
        @Body request: HackUpdate
    ): Response<HackSingleResponse>

    @DELETE("hacks/{id}")
    suspend fun deleteHack(@Path("id") id: Int): Response<ApiResponse<Map<String, String>>>

    // Voice Transcription
    @Multipart
    @POST("voice/transcribe")
    suspend fun transcribeVoice(
        @Part audioFile: MultipartBody.Part,
        @Part("language") language: RequestBody?
    ): Response<TranscriptionResponse>

    // Health
    @GET("/")
    suspend fun healthCheck(): Response<Map<String, String>>
}

data class UpdateRequest(
    val avatar: String? = null,
    val preferences: Map<String, Any>? = null
)
