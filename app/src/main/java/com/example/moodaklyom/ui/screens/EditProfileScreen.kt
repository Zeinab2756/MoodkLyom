package com.moodaklyom.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.ui.components.CustomTopAppBar
import kotlinx.coroutines.launch

@Composable
fun EditProfileScreen(
    navController: NavController,
    tokenManager: TokenManager = TokenManager(LocalContext.current)
) {
    // Load current username from DataStore
    val storedUsername by tokenManager.username.collectAsState(initial = "User")

    var username by remember(storedUsername) {
        mutableStateOf(storedUsername ?: "User")
    }

    var isSaving by remember { mutableStateOf(false) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = { CustomTopAppBar("Edit Profile") },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.Start
        ) {

            Text(
                text = "Update your profile information",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onBackground
            )

            OutlinedTextField(
                value = username,
                onValueChange = { username = it },
                label = { Text("Display name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(8.dp))

            val hasChanges = username.trim() != (storedUsername ?: "User").trim()
            val isValid = username.trim().isNotEmpty()

            Button(
                onClick = {
                    scope.launch {
                        try {
                            isSaving = true
                            // Save only username in DataStore
                            tokenManager.saveUsername(username.trim())
                            snackbarHostState.showSnackbar("Profile updated")
                            navController.popBackStack()
                        } finally {
                            isSaving = false
                        }
                    }
                },
                enabled = !isSaving && isValid && hasChanges,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                if (isSaving) {
                    CircularProgressIndicator(
                        strokeWidth = 2.dp,
                        modifier = Modifier.size(20.dp)
                    )
                } else {
                    Text("Save")
                }
            }
        }
    }
}
