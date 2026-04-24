package com.moodaklyom.data.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    // Change this to your backend URL
    // For Android Emulator: http://10.0.2.2:8000
    // For physical device: http://YOUR_COMPUTER_IP:8000
    //private const val BASE_URL = "http://10.0.2.2:8000/"
    private const val BASE_URL = "http://192.168.10.29:8000/"

    //base url for phone emulator: http://192.168.10.29:8000/

    @Volatile
    private var authToken: String? = null

    fun setAuthToken(token: String?) {
        authToken = token
    }

    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val token = authToken

        // Only set Content-Type for non-multipart requests
        val contentType = original.body?.contentType()?.toString()
        val requestBuilder = original.newBuilder()

        if (contentType?.contains("multipart") != true && contentType?.contains("application/octet-stream") != true) {
            requestBuilder.header("Content-Type", "application/json")
        }

        token?.let {
            requestBuilder.header("Authorization", "Bearer $it")
        }

        chain.proceed(requestBuilder.build())
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val apiService: ApiService = retrofit.create(ApiService::class.java)
}

