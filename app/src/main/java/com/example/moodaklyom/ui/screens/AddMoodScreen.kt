package com.moodaklyom.ui.screens

import android.Manifest
import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import com.moodaklyom.data.api.RetrofitClient
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.data.model.MoodCreate
import com.moodaklyom.data.model.TranscriptionResponse
import kotlinx.coroutines.flow.first
import com.moodaklyom.ui.components.CustomTopAppBar
import com.moodaklyom.ui.theme.MintPrimary
import com.moodaklyom.ui.theme.MintLight
import com.moodaklyom.ui.theme.White
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun AddMoodScreen(navController: NavController) {
    var selectedMood by remember { mutableStateOf(0) }
    var notes by remember { mutableStateOf("") }
    var isRecording by remember { mutableStateOf(false) }
    var isTranscribing by remember { mutableStateOf(false) }
    var transcriptionError by remember { mutableStateOf<String?>(null) }
    var detectedEmotionLabel by remember { mutableStateOf<String?>(null) }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    // Audio recording state
    var mediaRecorder: MediaRecorder? by remember { mutableStateOf(null) }
    var audioFile: File? by remember { mutableStateOf(null) }

    // Permissions
    val recordAudioPermission = rememberPermissionState(Manifest.permission.RECORD_AUDIO)
    val readStoragePermission = rememberPermissionState(
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_AUDIO
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }
    )

    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { pickedUri ->
            scope.launch {

                isTranscribing = true
                transcriptionError = null

                transcribeAudioFile(context, uri = pickedUri) { result ->

                    if (result.isSuccess) {
                        val response = result.getOrNull()

                        // ✅ USE transcribed_text (correct backend field)
                        if (response?.success == true && !response.transcribed_text.isNullOrBlank()) {

                            notes = response.transcribed_text

                            // ✅ Update emotion logic
                            detectedEmotionLabel = response.emotion?.primary_emotion

                            // ✅ Suggest mood level based on emotion
                            response.emotion?.primary_emotion?.lowercase()?.let { emotion ->
                                selectedMood = when (emotion) {
                                    "anger", "fear" -> 2
                                    "sadness", "disgust" -> 3
                                    "neutral" -> 5
                                    "joy", "love" -> 8
                                    "surprise" -> 9
                                    else -> selectedMood
                                }
                            }

                            transcriptionError = null

                        } else {
                            transcriptionError = "Transcription failed"
                        }

                    } else {
                        transcriptionError =
                            result.exceptionOrNull()?.message ?: "Failed to transcribe audio"
                    }

                    isTranscribing = false
                }
            }
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        CustomTopAppBar(
            title = "Add Mood",
            onBackClick = { navController.popBackStack() }
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            Text(
                "How are you feeling?",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MintPrimary
            )

            // Mood Selector
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    (1..5).forEach { level ->
                        MoodButton(
                            level = level,
                            isSelected = selectedMood == level,
                            onClick = { selectedMood = level }
                        )
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    (6..10).forEach { level ->
                        MoodButton(
                            level = level,
                            isSelected = selectedMood == level,
                            onClick = { selectedMood = level }
                        )
                    }
                }
            }

            // AI Helper Section - Fixed Purple background to Light Green
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer // This is now light green
                )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Can't figure it out? Our AI will help you out",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Medium
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Record Button
                        IconButton(
                            onClick = {
                                if (isRecording) {
                                    stopRecording(context, mediaRecorder, audioFile) { file ->
                                        audioFile = file
                                        isRecording = false

                                        file?.let {
                                            scope.launch {
                                                isTranscribing = true
                                                transcriptionError = null

                                                transcribeAudioFile(context, null, it) { result ->

                                                    if (result.isSuccess) {
                                                        val response = result.getOrNull()

                                                        if (response?.success == true && !response.transcribed_text.isNullOrBlank()) {

                                                            // ✅ Use transcribed_text
                                                            notes = response.transcribed_text

                                                            // ✅ Update emotion logic
                                                            detectedEmotionLabel = response.emotion?.primary_emotion

                                                            // ✅ Suggest mood level based on emotion
                                                            response.emotion?.primary_emotion?.lowercase()?.let { emotion ->
                                                                selectedMood = when (emotion) {
                                                                    "anger", "fear" -> 2
                                                                    "sadness", "disgust" -> 3
                                                                    "neutral" -> 5
                                                                    "joy", "love" -> 8
                                                                    "surprise" -> 9
                                                                    else -> selectedMood
                                                                }
                                                            }

                                                            transcriptionError = null

                                                        } else {
                                                            transcriptionError = "Transcription failed"
                                                        }

                                                    } else {
                                                        transcriptionError =
                                                            result.exceptionOrNull()?.message ?: "Failed to transcribe audio"
                                                    }

                                                    isTranscribing = false
                                                }
                                            }
                                        }
                                    }
                                } else {
                                    if (recordAudioPermission.status.isGranted) {
                                        notes = ""
                                        detectedEmotionLabel = null
                                        transcriptionError = null
                                        selectedMood = 0

                                        startRecording(context) { recorder, file ->
                                            mediaRecorder = recorder
                                            audioFile = file
                                            isRecording = true
                                        }

                                    } else {
                                        recordAudioPermission.launchPermissionRequest()
                                    }
                                }
                            },
                            modifier = Modifier.size(64.dp)
                        ){
                            Surface(
                                modifier = Modifier.size(64.dp),
                                shape = CircleShape,
                                color = if (isRecording) MaterialTheme.colorScheme.error else MintPrimary
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Mic,
                                    contentDescription = if (isRecording) "Stop Recording" else "Record Voice",
                                    tint = White,
                                    modifier = Modifier.padding(16.dp)
                                )
                            }
                        }

                        // Upload Button
                        IconButton(
                            onClick = {
                                if (readStoragePermission.status.isGranted) {
                                    isTranscribing = true
                                    filePickerLauncher.launch("audio/*")
                                } else {
                                    readStoragePermission.launchPermissionRequest()
                                }
                            },
                            modifier = Modifier.size(64.dp)
                        ) {
                            Surface(
                                modifier = Modifier.size(64.dp),
                                shape = CircleShape,
                                color = MintPrimary
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Add,
                                    contentDescription = "Upload Audio",
                                    tint = White,
                                    modifier = Modifier.padding(16.dp)
                                )
                            }
                        }
                    }

                    if (isTranscribing) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth(), color = MintPrimary)
                        Text(
                            text = "Transcribing...",
                            style = MaterialTheme.typography.bodySmall
                        )
                    }

                    transcriptionError?.let { error ->
                        Text(
                            text = error,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(top = 8.dp)
                        )
                    }
                }
            }

            // Enhanced Notes Input
            OutlinedTextField(
                value = notes,
                onValueChange = { notes = it },
                label = { Text("Notes (optional)") },
                placeholder = { Text("How was your day? Write or record your thoughts...") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(150.dp),
                maxLines = 5,
                enabled = !isTranscribing,
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MintPrimary,
                    focusedLabelColor = MintPrimary,
                    cursorColor = MintPrimary,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                    focusedContainerColor = MaterialTheme.colorScheme.surface
                )
            )

            // Detected Emotion
            detectedEmotionLabel?.let { emotionName ->
                Text(
                    text = "Your emotion is: $emotionName",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = MintPrimary
                )
            }

            // Save Button
            Button(
                onClick = {
                    scope.launch {
                        try {
                            val tokenManager = TokenManager(context)
                            val token = tokenManager.token.first()
                            RetrofitClient.setAuthToken(token)

                            val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
                            val emoji = when (selectedMood) {
                                1 -> "😢"
                                2 -> "😣"
                                3 -> "😥"
                                4 -> "😕"
                                5 -> "😐"
                                6 -> "🙂"
                                7 -> "😎"
                                8 -> "🤭"
                                9 -> "☺️"
                                10 -> "😄"
                                else -> "😐"
                            }

                            val moodLevel = when {
                                selectedMood <= 2 -> 1
                                selectedMood <= 4 -> 2
                                selectedMood <= 6 -> 3
                                selectedMood <= 8 -> 4
                                else -> 5
                            }

                            val request = MoodCreate(
                                date = today,
                                moodLevel = moodLevel,
                                emoji = emoji,
                                emotion = detectedEmotionLabel,
                                notes = if (notes.isBlank()) null else notes
                            )

                            val response = RetrofitClient.apiService.addMood(request)
                            if (response.isSuccessful && response.body() != null) {
                                navController.popBackStack()
                            } else {
                                transcriptionError = response.errorBody()?.string() ?: "Failed to save mood"
                            }
                        } catch (e: Exception) {
                            transcriptionError = e.message ?: "Failed to save mood"
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                enabled = selectedMood > 0 && !isTranscribing,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MintPrimary,
                    contentColor = White
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Text("Save Mood", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
fun MoodButton(level: Int, isSelected: Boolean, onClick: () -> Unit) {
    val emoji = when (level) {
        1 -> "😢"
        2 -> "😣"
        3 -> "😥"
        4 -> "😕"
        5 -> "😐"
        6 -> "🙂"
        7 -> "😎"
        8 -> "🤭"
        9 -> "☺️"
        10 -> "😄"
        else -> "😐"
    }

    Surface(
        onClick = onClick,
        modifier = Modifier.size(64.dp),
        shape = RoundedCornerShape(16.dp),
        color = if (isSelected) MintPrimary else MaterialTheme.colorScheme.surface,
        border = if (!isSelected) {
            androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
        } else null
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(emoji, style = MaterialTheme.typography.headlineMedium)
        }
    }
}

// Helper functions for audio recording and transcription

fun startRecording(context: Context, onStarted: (MediaRecorder, File) -> Unit) {
    try {
        val audioDir = File(context.cacheDir, "audio_recordings")
        if (!audioDir.exists()) {
            audioDir.mkdirs()
        }

        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val audioFile = File(audioDir, "recording_$timestamp.m4a")

        val mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioEncodingBitRate(128000)
            setAudioSamplingRate(44100)
            setOutputFile(audioFile.absolutePath)

            try {
                prepare()
                start()
                onStarted(this, audioFile)
            } catch (e: IOException) {
                e.printStackTrace()
                release()
            }
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

fun stopRecording(context: Context, mediaRecorder: MediaRecorder?, audioFile: File?, onStopped: (File?) -> Unit) {
    try {
        mediaRecorder?.apply {
            stop()
            release()
        }
        onStopped(audioFile)
    } catch (e: Exception) {
        e.printStackTrace()
        onStopped(null)
    }
}

suspend fun transcribeAudioFile(
    context: Context,
    uri: android.net.Uri? = null,
    file: File? = null,
    onResult: (Result<TranscriptionResponse>) -> Unit
) {
    try {
        val audioFile = file ?: run {
            uri?.let {
                val inputStream = context.contentResolver.openInputStream(it)
                val tempFile = File(context.cacheDir, "temp_audio_${System.currentTimeMillis()}.m4a")
                inputStream?.use { input ->
                    tempFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                tempFile
            }
        }

        if (audioFile == null || !audioFile.exists()) {
            onResult(Result.failure(Exception("Audio file not found")))
            return
        }

        val tokenManager = TokenManager(context)
        val token = tokenManager.token.first()
        RetrofitClient.setAuthToken(token)

        val fileName = if (audioFile.name.endsWith(".m4a") || audioFile.name.endsWith(".mp3") ||
            audioFile.name.endsWith(".wav") || audioFile.name.endsWith(".ogg")) {
            audioFile.name
        } else {
            "${audioFile.name}.m4a"
        }
        val requestFile = audioFile.asRequestBody("audio/m4a".toMediaTypeOrNull())
        val audioPart = MultipartBody.Part.createFormData("audio_file", fileName, requestFile)

        val response = RetrofitClient.apiService.transcribeVoice(audioPart, null)

        if (response.isSuccessful && response.body() != null) {
            onResult(Result.success(response.body()!!))
        } else {
            val errorMsg = response.errorBody()?.string() ?: "Transcription failed"
            onResult(Result.failure(Exception(errorMsg)))
        }

        if (uri != null && audioFile.exists()) {
            audioFile.delete()
        }
    } catch (e: Exception) {
        onResult(Result.failure(e))
    }
}
