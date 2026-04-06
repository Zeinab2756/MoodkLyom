package com.moodaklyom

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.moodaklyom.data.api.RetrofitClient
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.data.model.TaskResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class TasksUiState(
    val isLoading: Boolean = true,
    val tasks: List<TaskResponse> = emptyList(),
    val error: String? = null,
    val togglingIds: Set<Int> = emptySet()
)

class TasksViewModel(private val tokenManager: TokenManager) : ViewModel() {

    private val _uiState = MutableStateFlow(TasksUiState())
    val uiState: StateFlow<TasksUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val token = tokenManager.token.first()
                RetrofitClient.setAuthToken(token)

                val response = RetrofitClient.apiService.getTasks(limit = 100)
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body?.success == true) {
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                tasks = body.data,
                                error = null
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                error = "No tasks available yet.",
                                tasks = emptyList()
                            )
                        }
                    }
                } else {
                    val msg = response.errorBody()?.string() ?: "Failed to load tasks"
                    _uiState.update { it.copy(isLoading = false, error = msg) }
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.message ?: "Unexpected error fetching tasks"
                    )
                }
            }
        }
    }

    fun toggleTask(id: Int) {
        viewModelScope.launch {
            _uiState.update { it.copy(togglingIds = it.togglingIds + id) }
            try {
                val token = tokenManager.token.first()
                RetrofitClient.setAuthToken(token)

                val response = RetrofitClient.apiService.toggleTask(id)
                if (response.isSuccessful) {
                    val body = response.body()
                    val updated = body?.data
                    if (body?.success == true && updated != null) {
                        _uiState.update {
                            it.copy(
                                tasks = it.tasks.map { task ->
                                    if (task.id == id) updated else task
                                },
                                togglingIds = it.togglingIds - id
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(
                                error = "Could not toggle task.",
                                togglingIds = it.togglingIds - id
                            )
                        }
                    }
                } else {
                    val msg = response.errorBody()?.string() ?: "Toggle failed"
                    _uiState.update {
                        it.copy(error = msg, togglingIds = it.togglingIds - id)
                    }
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        error = e.message ?: "Toggle failed",
                        togglingIds = it.togglingIds - id
                    )
                }
            }
        }
    }
}
