package com.moodaklyom.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = MintPrimary,
    secondary = MintSecondary,
    tertiary = MintLight,
    background = Color(0xFF1A1C1A),
    surface = Color(0xFF2D2E2D),
    onPrimary = Color(0xFF1B3726),
    onSecondary = Color(0xFF1B3726),
    onBackground = Color(0xFFE1E3DF),
    onSurface = Color(0xFFE1E3DF),
    primaryContainer = MintDark,
    onPrimaryContainer = MintLight,
    surfaceVariant = Color(0xFF3E4A42),
    onSurfaceVariant = MintLight
)

private val LightColorScheme = lightColorScheme(
    primary = MintPrimary,
    secondary = MintSecondary,
    tertiary = MintLight,
    background = WhiteBackground,
    surface = White,
    onPrimary = Color(0xFFFFFFFF),
    onSecondary = Color(0xFFFFFFFF),
    onBackground = MintDark,
    onSurface = MintDark,
    primaryContainer = Color(0xFFE8F5E9), // Light green container
    onPrimaryContainer = MintDark,
    surfaceVariant = Color(0xFFE8F5E9), // Light green for cards, fixed from purple
    onSurfaceVariant = MintDark
)

@Composable
fun MoodakLyomTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false, // Set to false to force our mint theme
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = androidx.compose.material3.Typography(),
        content = content
    )
}
