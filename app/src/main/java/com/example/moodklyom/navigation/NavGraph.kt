package com.example.moodklyom.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.NavHostController
import androidx.navigation.navArgument
import androidx.navigation.navDeepLink
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.moodklyom.ui.screens.*

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Home : Screen("home")
    object Moods : Screen("moods")
    object AddMood : Screen("add_mood")
    object Tasks : Screen("tasks")
    object AddTask : Screen("add_task")
    object Hacks : Screen("hacks")
    object Profile : Screen("profile")
    object Settings : Screen("settings")
    object About : Screen("about")
    object EditProfile : Screen("edit_profile")
    object ChangePassword : Screen("change_password")
}

@Composable
fun NavGraph(
    navController: NavHostController,
    isDarkTheme: Boolean,
    onDarkThemeChange: (Boolean) -> Unit
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Login.route
    ) {
        composable(Screen.Login.route) {
            LoginScreen(navController = navController)
        }
        composable(Screen.Home.route) {
            HomeScreen(navController = navController)
        }
        composable(Screen.Moods.route) {
            MoodsScreen(navController = navController)
        }
        composable(Screen.AddMood.route) {
            AddMoodScreen(navController = navController)
        }
        composable(
            route = "${Screen.Tasks.route}?proposedIds={proposedIds}",
            arguments = listOf(
                navArgument("proposedIds") {
                    type = NavType.StringType
                    defaultValue = ""
                }
            ),
            deepLinks = listOf(
                navDeepLink {
                    uriPattern = "moodaklyom://tasks?proposedIds={proposedIds}"
                }
            )
        ) { backStackEntry ->
            val proposedIds = backStackEntry.arguments
                ?.getString("proposedIds")
                .orEmpty()
                .split(",")
                .mapNotNull { it.toIntOrNull() }
                .toSet()
            TasksScreen(
                navController = navController,
                proposedTaskIds = proposedIds
            )
        }
        composable(Screen.AddTask.route) {
            AddTaskScreen(navController = navController)
        }
        composable(Screen.Hacks.route) {
            HacksScreen(navController = navController)
        }
        composable(Screen.Profile.route) {
            ProfileScreen(navController = navController)
        }
        composable(Screen.Settings.route) {
            SettingsScreen(
                navController = navController,
                isDarkTheme = isDarkTheme,
                onDarkThemeChange = onDarkThemeChange
            )
        }
        composable(Screen.About.route) {
            AboutScreen(navController = navController)
        }
        composable(Screen.EditProfile.route) {
            EditProfileScreen(navController = navController)
        }
        composable(Screen.ChangePassword.route) {
            ChangePasswordScreen(navController = navController)
        }
    }
}
