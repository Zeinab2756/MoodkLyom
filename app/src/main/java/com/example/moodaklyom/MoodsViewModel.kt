package com.moodaklyom

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.moodaklyom.data.api.RetrofitClient
import com.moodaklyom.data.local.TokenManager
import com.moodaklyom.data.model.MoodResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MoodsUiState(
    val isLoading: Boolean = true,
    val moods: List<MoodResponse> = emptyList(),
    val error: String? = null
)

class MoodsViewModel(private val tokenManager: TokenManager) : ViewModel() {

    private val _uiState = MutableStateFlow(MoodsUiState())
    val uiState: StateFlow<MoodsUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val token = tokenManager.token.first()
                RetrofitClient.setAuthToken(token)

                val response = RetrofitClient.apiService.getAllMoods()
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                moods = body.moods,
                                error = null
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                moods = emptyList(),
                                error = "No moods available yet."
                            )
                        }
                    }
                } else {
                    val msg = response.errorBody()?.string() ?: "Failed to load moods"
                    _uiState.update { it.copy(isLoading = false, error = msg) }
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.message ?: "Unexpected error fetching moods"
                    )
                }
            }
        }
    }
}
