package com.moodaklyom.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.moodaklyom.ui.components.CustomTopAppBar



@Composable
fun ChangePasswordScreen(navController: NavController) {
    CustomTopAppBar("Change Password")
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.Top,
        horizontalAlignment = Alignment.Start
    ) {
        Text(
            text = "Change Password Screen (TODO: add fields)",
            style = MaterialTheme.typography.bodyLarge
        )
    }
}
