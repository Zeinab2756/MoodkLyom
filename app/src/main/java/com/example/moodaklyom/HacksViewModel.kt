package com.moodaklyom

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.moodaklyom.data.api.RetrofitClient
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.data.model.WellnessTip
import com.moodaklyom.data.model.TaskCreate
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class HacksUiState(
    val isLoading: Boolean = true,
    val hacks: List<WellnessTip> = emptyList(),
    val error: String? = null,
    val creatingTaskIds: Set<Int> = emptySet()
)

class HacksViewModel(private val tokenManager: TokenManager) : ViewModel() {

    private val _uiState = MutableStateFlow(HacksUiState())
    val uiState: StateFlow<HacksUiState> = _uiState.asStateFlow()

    init {
        loadHacks()
    }

    fun refresh() {
        loadHacks()
    }

    private fun loadHacks() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                // Ensure requests use the persisted auth token (if available)
                val token = tokenManager.token.first()
                RetrofitClient.setAuthToken(token)

                val response = RetrofitClient.apiService.getWellnessTips()

                if (!response.isSuccessful) {
                    val errorBody = response.errorBody()?.string()
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = "Failed to load tips: ${errorBody ?: response.code()}"
                        )
                    }
                    return@launch
                }

                val body = response.body()
                if (body != null && body.isNotEmpty()) {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            hacks = body,
                            error = null,
                            creatingTaskIds = emptySet()
                        )
                    }
                } else {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = "No tips available yet."
                        )
                    }
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = "Could not load tips: ${e.message}"
                    )
                }
            }
        }
    }

    fun addHackAsTask(hack: WellnessTip) {
        viewModelScope.launch {
            _uiState.update { it.copy(creatingTaskIds = it.creatingTaskIds + hack.id) }
            try {
                val token = tokenManager.token.first()
                RetrofitClient.setAuthToken(token)

                val response = RetrofitClient.apiService.createTask(
                    TaskCreate(
                        title = hack.title,
                        description = hack.description,
                        priority = "MEDIUM"
                    )
                )

                if (response.isSuccessful && response.body()?.success == true) {
                    _uiState.update { it.copy(creatingTaskIds = it.creatingTaskIds - hack.id) }
                } else {
                    val msg = response.errorBody()?.string() ?: "Failed to add to tasks"
                    _uiState.update {
                        it.copy(
                            error = msg,
                            creatingTaskIds = it.creatingTaskIds - hack.id
                        )
                    }
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        error = e.message ?: "Failed to add to tasks",
                        creatingTaskIds = it.creatingTaskIds - hack.id
                    )
                }
            }
        }
    }
}
