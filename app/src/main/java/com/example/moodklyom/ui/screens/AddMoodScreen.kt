package com.example.moodklyom.ui.screens

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.navigation.NavController
import com.example.moodklyom.MainActivity
import com.example.moodklyom.data.api.RetrofitClient
import com.example.moodklyom.data.local.TokenManager
import com.example.moodklyom.data.model.MoodAnalysisResponse
import com.example.moodklyom.data.model.MoodCreate
import com.example.moodklyom.data.model.TaskCreate
import com.example.moodklyom.ui.components.CustomTopAppBar
import com.example.moodklyom.ui.theme.MintPrimary
import com.example.moodklyom.ui.theme.White
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.OptIn

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

    var mediaRecorder: MediaRecorder? by remember { mutableStateOf(null) }
    var audioFile: File? by remember { mutableStateOf(null) }

    val recordAudioPermission = rememberPermissionState(Manifest.permission.RECORD_AUDIO)
    val readStoragePermission = rememberPermissionState(
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_AUDIO
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }
    )
    val notificationPermission = rememberPermissionState(Manifest.permission.POST_NOTIFICATIONS)

    LaunchedEffect(Unit) {
        if (
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            !notificationPermission.status.isGranted
        ) {
            notificationPermission.launchPermissionRequest()
        }
    }

    fun applyMoodAnalysis(response: MoodAnalysisResponse) {
        if (!response.transcript.isNullOrBlank()) {
            notes = response.transcript
        }
        detectedEmotionLabel = formatMoodLabel(response.mood)
        selectedMood = moodLabelToSliderValue(response.mood)
        transcriptionError = if (response.degraded && response.warnings.isNotEmpty()) {
            response.warnings.joinToString("\n")
        } else {
            null
        }
    }

    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        if (uri == null) {
            isTranscribing = false
        } else {
            scope.launch {
                isTranscribing = true
                transcriptionError = null

                analyzeAudioWithAi(context, uri = uri) { result ->
                    if (result.isSuccess) {
                        applyMoodAnalysis(result.getOrThrow())
                    } else {
                        transcriptionError =
                            result.exceptionOrNull()?.message ?: "Failed to analyze audio"
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
                .padding(horizontal = 24.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            Text(
                "How are you feeling?",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MintPrimary
            )

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

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
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
                        IconButton(
                            onClick = {
                                if (isRecording) {
                                    stopRecording(mediaRecorder, audioFile) { file ->
                                        audioFile = file
                                        isRecording = false

                                        file?.let { recordedFile ->
                                            scope.launch {
                                                isTranscribing = true
                                                transcriptionError = null

                                                analyzeAudioWithAi(context, file = recordedFile) { result ->
                                                    if (result.isSuccess) {
                                                        applyMoodAnalysis(result.getOrThrow())
                                                    } else {
                                                        transcriptionError =
                                                            result.exceptionOrNull()?.message
                                                                ?: "Failed to analyze audio"
                                                    }
                                                    isTranscribing = false
                                                }
                                            }
                                        }
                                    }
                                } else if (recordAudioPermission.status.isGranted) {
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
                            },
                            modifier = Modifier.size(64.dp)
                        ) {
                            Surface(
                                modifier = Modifier.size(64.dp),
                                shape = CircleShape,
                                color = if (isRecording) {
                                    MaterialTheme.colorScheme.error
                                } else {
                                    MintPrimary
                                }
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Mic,
                                    contentDescription = if (isRecording) {
                                        "Stop Recording"
                                    } else {
                                        "Record Voice"
                                    },
                                    tint = White,
                                    modifier = Modifier.padding(16.dp)
                                )
                            }
                        }

                        IconButton(
                            onClick = {
                                if (readStoragePermission.status.isGranted) {
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
                        LinearProgressIndicator(
                            modifier = Modifier.fillMaxWidth(),
                            color = MintPrimary
                        )
                        Text(
                            text = "Analyzing voice...",
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

            detectedEmotionLabel?.let { moodName ->
                Text(
                    text = "Your emotion is: $moodName",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = MintPrimary
                )
            }

            Button(
                onClick = {
                    scope.launch {
                        try {
                            val tokenManager = TokenManager(context)
                            val token = tokenManager.token.first()
                            RetrofitClient.setAuthToken(token)

                            val today = SimpleDateFormat(
                                "yyyy-MM-dd",
                                Locale.getDefault()
                            ).format(Date())

                            val request = MoodCreate(
                                date = today,
                                moodLevel = moodLevelForSlider(selectedMood),
                                emoji = moodEmojiForLevel(selectedMood),
                                emotion = moodEmotionForLevel(selectedMood),
                                notes = notes.takeIf { it.isNotBlank() }
                            )

                            val response = RetrofitClient.apiService.addMood(request)
                            if (response.isSuccessful && response.body() != null) {
                                if (
                                    Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                                    !notificationPermission.status.isGranted
                                ) {
                                    notificationPermission.launchPermissionRequest()
                                }

                                val proposedTaskIds = createProposedTasksForMood(
                                    mood = request.emotion ?: "neutral"
                                )
                                if (proposedTaskIds.isNotEmpty()) {
                                    showProposedTasksNotification(context, proposedTaskIds)
                                }
                                navController.popBackStack()
                            } else {
                                transcriptionError =
                                    response.errorBody()?.string() ?: "Failed to save mood"
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
    Surface(
        onClick = onClick,
        modifier = Modifier.size(64.dp),
        shape = RoundedCornerShape(16.dp),
        color = if (isSelected) MintPrimary else MaterialTheme.colorScheme.surface,
        border = if (!isSelected) {
            BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
        } else {
            null
        }
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(moodEmojiForLevel(level), style = MaterialTheme.typography.headlineMedium)
        }
    }
}

private fun formatMoodLabel(label: String): String {
    return label
        .replace('_', ' ')
        .replace('-', ' ')
        .trim()
        .split(Regex("\\s+"))
        .filter { it.isNotBlank() }
        .joinToString(" ") { part ->
            part.lowercase().replaceFirstChar { char ->
                if (char.isLowerCase()) char.titlecase(Locale.getDefault()) else char.toString()
            }
        }
}

private fun moodLabelToSliderValue(label: String): Int {
    return when (label.trim().lowercase(Locale.getDefault())) {
        "happy" -> 9
        "surprised" -> 8
        "neutral" -> 5
        "sad" -> 2
        "fearful" -> 2
        "angry" -> 3
        "disgusted" -> 3
        else -> 5
    }
}

private fun moodLevelForSlider(selectedMood: Int): Int {
    return when {
        selectedMood <= 2 -> 1
        selectedMood <= 4 -> 2
        selectedMood <= 6 -> 3
        selectedMood <= 8 -> 4
        else -> 5
    }
}

private fun moodEmojiForLevel(level: Int): String {
    return when (level) {
        1 -> "\uD83D\uDE22"
        2 -> "\uD83D\uDE23"
        3 -> "\uD83D\uDE25"
        4 -> "\uD83D\uDE15"
        5 -> "\uD83D\uDE10"
        6 -> "\uD83D\uDE42"
        7 -> "\uD83D\uDE0E"
        8 -> "\uD83E\uDD2D"
        9 -> "\u263A\uFE0F"
        10 -> "\uD83D\uDE04"
        else -> "\uD83D\uDE10"
    }
}

private fun moodEmotionForLevel(level: Int): String {
    return when (level) {
        1 -> "sad"
        2 -> "frustrated"
        3 -> "anxious"
        4 -> "confused"
        5 -> "neutral"
        6 -> "content"
        7 -> "confident"
        8 -> "playful"
        9 -> "happy"
        10 -> "happy"
        else -> "neutral"
    }
}

suspend fun createProposedTasksForMood(mood: String): List<Int> {
    val proposalsResponse = RetrofitClient.apiService.getProposedTasks(mood = mood, limit = 3)
    if (!proposalsResponse.isSuccessful || proposalsResponse.body()?.success != true) {
        return emptyList()
    }

    return proposalsResponse.body()!!
        .data
        .mapNotNull { proposed ->
            val createResponse = RetrofitClient.apiService.createTask(
                TaskCreate(
                    title = proposed.title,
                    description = proposed.description,
                    priority = proposed.priority
                )
            )
            if (createResponse.isSuccessful && createResponse.body()?.success == true) {
                createResponse.body()?.data?.id
            } else {
                null
            }
        }
}

private fun showProposedTasksNotification(context: Context, taskIds: List<Int>) {
    val channelId = "proposed_tasks"
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(
            channelId,
            "Proposed Tasks",
            NotificationManager.IMPORTANCE_DEFAULT
        )
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    if (
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.POST_NOTIFICATIONS
        ) != PackageManager.PERMISSION_GRANTED
    ) {
        return
    }

    val deepLink = Uri.parse("moodaklyom://tasks?proposedIds=${taskIds.joinToString(",")}")
    val intent = Intent(Intent.ACTION_VIEW, deepLink, context, MainActivity::class.java).apply {
        flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
    }
    val pendingIntent = PendingIntent.getActivity(
        context,
        2001,
        intent,
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )

    val notification = NotificationCompat.Builder(context, channelId)
        .setSmallIcon(android.R.drawable.ic_dialog_info)
        .setContentTitle("Your suggested tasks are ready")
        .setContentText("Tap to see the tasks proposed from your mood.")
        .setContentIntent(pendingIntent)
        .setAutoCancel(true)
        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        .build()

    NotificationManagerCompat.from(context).notify(2001, notification)
}

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

fun stopRecording(mediaRecorder: MediaRecorder?, audioFile: File?, onStopped: (File?) -> Unit) {
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

suspend fun analyzeAudioWithAi(
    context: Context,
    uri: Uri? = null,
    file: File? = null,
    onResult: (Result<MoodAnalysisResponse>) -> Unit
) {
    try {
        val audioFile = file ?: uri?.let { sourceUri ->
            val inputStream = context.contentResolver.openInputStream(sourceUri)
            val tempFile = File(context.cacheDir, "temp_audio_${System.currentTimeMillis()}.m4a")
            inputStream?.use { input ->
                tempFile.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            tempFile
        }

        if (audioFile == null || !audioFile.exists()) {
            onResult(Result.failure(Exception("Audio file not found")))
            return
        }

        val tokenManager = TokenManager(context)
        val token = tokenManager.token.first()
        RetrofitClient.setAuthToken(token)

        val fileName = ensureSupportedAudioExtension(audioFile.name)
        val requestFile = audioFile
            .asRequestBody(audioMediaTypeForFile(fileName).toMediaTypeOrNull())
        val audioPart = MultipartBody.Part.createFormData("audio_file", fileName, requestFile)

        val response = RetrofitClient.apiService.analyzeMood(audioPart, null)
        if (response.isSuccessful && response.body() != null) {
            onResult(Result.success(response.body()!!))
        } else {
            val errorMsg = response.errorBody()?.string() ?: "Mood analysis failed"
            onResult(Result.failure(Exception(errorMsg)))
        }

        if (uri != null && audioFile.exists()) {
            audioFile.delete()
        }
    } catch (e: Exception) {
        onResult(Result.failure(e))
    }
}

private fun ensureSupportedAudioExtension(fileName: String): String {
    return if (
        fileName.endsWith(".m4a", ignoreCase = true) ||
        fileName.endsWith(".mp3", ignoreCase = true) ||
        fileName.endsWith(".wav", ignoreCase = true) ||
        fileName.endsWith(".ogg", ignoreCase = true)
    ) {
        fileName
    } else {
        "$fileName.m4a"
    }
}

private fun audioMediaTypeForFile(fileName: String): String {
    return when {
        fileName.endsWith(".wav", ignoreCase = true) -> "audio/wav"
        fileName.endsWith(".mp3", ignoreCase = true) -> "audio/mpeg"
        fileName.endsWith(".ogg", ignoreCase = true) -> "audio/ogg"
        else -> "audio/mp4"
    }
}
