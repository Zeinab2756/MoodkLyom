package com.moodaklyom.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.moodaklyom.ui.components.CustomTopAppBar
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(
    navController: NavController,
    isDarkTheme: Boolean,
    onDarkThemeChange: (Boolean) -> Unit
) {
    // Local state copies (will be applied when the user taps Save)
    var darkMode by remember { mutableStateOf(isDarkTheme) }
    var notificationsEnabled by remember { mutableStateOf(true) }
    var emailNotificationsEnabled by remember { mutableStateOf(false) }
    var vibrationEnabled by remember { mutableStateOf(true) }

    val snackbarHostState = remember { SnackbarHostState() }
    val coroutineScope = rememberCoroutineScope()

    Scaffold(
        topBar = { 
            CustomTopAppBar(
                title = "Settings",
                onBackClick = { navController.popBackStack() }
            ) 
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {

            // ===== GENERAL =====
            SettingsSectionTitle(title = "General")

            SettingsSwitchRow(
                title = "Dark mode",
                description = "Use dark theme throughout the app",
                checked = darkMode,
                onCheckedChange = { darkMode = it }
            )

            SettingsClickableRow(
                title = "Language",
                description = "App language",
                onClick = {
                    // TODO: navController.navigate("language")
                }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // ===== NOTIFICATIONS =====
            SettingsSectionTitle(title = "Notifications")

            SettingsSwitchRow(
                title = "Push notifications",
                description = "Receive updates and reminders",
                checked = notificationsEnabled,
                onCheckedChange = { notificationsEnabled = it }
            )

            SettingsSwitchRow(
                title = "Email notifications",
                description = "Get summaries by email",
                checked = emailNotificationsEnabled,
                onCheckedChange = { emailNotificationsEnabled = it }
            )

            SettingsSwitchRow(
                title = "Vibration",
                description = "Vibrate on important alerts",
                checked = vibrationEnabled,
                onCheckedChange = { vibrationEnabled = it }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // ===== ACCOUNT =====
            SettingsSectionTitle(title = "Account")

            SettingsClickableRow(
                title = "Edit profile",
                description = "Name, photo, and bio",
                onClick = {
                    navController.navigate("edit_profile")
                }
            )

            SettingsClickableRow(
                title = "Change password",
                description = "Update your password",
                onClick = {
                    navController.navigate("change_password")
                }
            )

            SettingsClickableRow(
                title = "Privacy & security",
                description = "Blocked users, data & permissions",
                onClick = {
                    // TODO: navController.navigate("privacy")
                }
            )

            Spacer(modifier = Modifier.height(16.dp))

            // ===== ABOUT =====
            SettingsSectionTitle(title = "About")

            SettingsClickableRow(
                title = "About MoodakLyom",
                description = "Version 1.0.0 • Learn more",
                onClick = {
                    // TODO: navController.navigate("about")
                }
            )

            SettingsClickableRow(
                title = "Terms of use",
                onClick = {
                    // TODO: navController.navigate("terms")
                }
            )

            SettingsClickableRow(
                title = "Privacy policy",
                onClick = {
                    // TODO: navController.navigate("privacy_policy")
                }
            )

            Spacer(modifier = Modifier.height(24.dp))

            // ===== SAVE BUTTON =====
            Button(
                onClick = {
                    // Apply settings
                    onDarkThemeChange(darkMode)
                    // Later: persist notificationsEnabled, emailNotificationsEnabled, vibrationEnabled
                    // using DataStore or a ViewModel

                    coroutineScope.launch {
                        snackbarHostState.showSnackbar("Settings saved")
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                Text("Save")
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

// ---------- Helper Composables ----------

@Composable
private fun SettingsSectionTitle(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.SemiBold),
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp)
    )
}

@Composable
private fun SettingsSwitchRow(
    title: String,
    description: String? = null,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge
                )
                if (description != null) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = description,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange
            )
        }
        HorizontalDivider(modifier = Modifier.padding(top = 8.dp))
    }
}

@Composable
private fun SettingsClickableRow(
    title: String,
    description: String? = null,
    onClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(vertical = 8.dp)
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.bodyLarge
        )
        if (description != null) {
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        HorizontalDivider(modifier = Modifier.padding(top = 8.dp))
    }
}
