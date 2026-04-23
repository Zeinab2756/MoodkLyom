package com.moodaklyom.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.moodaklyom.data.api.RetrofitClient
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.data.model.TaskCreate
import com.moodaklyom.ui.components.CustomTopAppBar
import com.moodaklyom.ui.theme.MintPrimary
import com.moodaklyom.ui.theme.White
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

@Composable
fun AddTaskScreen(navController: NavController) {
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var selectedPriority by remember { mutableStateOf("MEDIUM") }
    var isSaving by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val priorities = listOf("LOW", "MEDIUM", "HIGH", "URGENT")
    val context = LocalContext.current
    val tokenManager = remember { TokenManager(context) }
    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize()) {
        CustomTopAppBar(
            title = "Add Task",
            onBackClick = { navController.popBackStack() }
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // Styled Title Input
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("Task Title") },
                placeholder = { Text("What needs to be done?") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MintPrimary,
                    focusedLabelColor = MintPrimary,
                    cursorColor = MintPrimary,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                    focusedContainerColor = MaterialTheme.colorScheme.surface
                )
            )

            // Styled Description Input
            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Description (optional)") },
                placeholder = { Text("Add more details...") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(150.dp),
                maxLines = 5,
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MintPrimary,
                    focusedLabelColor = MintPrimary,
                    cursorColor = MintPrimary,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                    focusedContainerColor = MaterialTheme.colorScheme.surface
                )
            )

            Text(
                "Priority",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MintPrimary
            )

            // Priority Grid: 2 by 2
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // First Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    PriorityButton(
                        text = "LOW",
                        isSelected = selectedPriority == "LOW",
                        onClick = { selectedPriority = "LOW" },
                        modifier = Modifier.weight(1f)
                    )
                    PriorityButton(
                        text = "MEDIUM",
                        isSelected = selectedPriority == "MEDIUM",
                        onClick = { selectedPriority = "MEDIUM" },
                        modifier = Modifier.weight(1f)
                    )
                }
                // Second Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    PriorityButton(
                        text = "HIGH",
                        isSelected = selectedPriority == "HIGH",
                        onClick = { selectedPriority = "HIGH" },
                        modifier = Modifier.weight(1f)
                    )
                    PriorityButton(
                        text = "URGENT",
                        isSelected = selectedPriority == "URGENT",
                        onClick = { selectedPriority = "URGENT" },
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            errorMessage?.let { msg ->
                Text(
                    text = msg,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = {
                    scope.launch {
                        try {
                            isSaving = true
                            errorMessage = null

                            val token = tokenManager.token.first()
                            RetrofitClient.setAuthToken(token)

                            val request = TaskCreate(
                                title = title,
                                description = description.ifBlank { null },
                                priority = selectedPriority
                            )

                            val response = RetrofitClient.apiService.createTask(request)
                            if (response.isSuccessful && response.body()?.success == true) {
                                navController.popBackStack()
                            } else {
                                val msg =
                                    response.errorBody()?.string() ?: "Failed to create task."
                                errorMessage = msg
                            }
                        } catch (e: Exception) {
                            errorMessage = e.message ?: "Failed to create task."
                        } finally {
                            isSaving = false
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                enabled = title.isNotBlank() && !isSaving,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MintPrimary,
                    contentColor = White
                ),
                shape = RoundedCornerShape(16.dp),
                elevation = ButtonDefaults.buttonElevation(defaultElevation = 4.dp)
            ) {
                if (isSaving) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = White,
                        strokeWidth = 3.dp
                    )
                } else {
                    Text(
                        "Save Task", 
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
fun PriorityButton(
    text: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(52.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isSelected) MintPrimary else MaterialTheme.colorScheme.surface,
            contentColor = if (isSelected) White else MaterialTheme.colorScheme.onSurface
        ),
        shape = RoundedCornerShape(16.dp),
        border = if (!isSelected) {
            androidx.compose.foundation.BorderStroke(1.dp, MintPrimary.copy(alpha = 0.3f))
        } else null,
        elevation = if (isSelected) ButtonDefaults.buttonElevation(defaultElevation = 4.dp) else null,
        contentPadding = PaddingValues(0.dp)
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge.copy(fontSize = 15.sp),
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold
        )
    }
}
