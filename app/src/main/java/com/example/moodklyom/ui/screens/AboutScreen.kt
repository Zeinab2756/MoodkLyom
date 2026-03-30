package com.moodaklyom.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.navigation.NavController
import com.moodaklyom.ui.components.CustomTopAppBar

@Composable
fun AboutScreen(navController: NavController) {
    CustomTopAppBar("About")
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Text("MoodakLyom v1.0\nDeveloped with ❤️")
    }
}
