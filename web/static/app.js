// Shared JavaScript functionality for the Food Recommendation System

// Utility functions
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const messageEl = document.getElementById('loading-message');
    if (messageEl) messageEl.textContent = message;
    if (overlay) overlay.classList.remove('hidden');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    if (!container) return;
    
    const messageEl = document.createElement('div');
    const baseClasses = 'px-6 py-4 rounded-lg shadow-lg mb-4 transition-all duration-300 transform';
    
    switch(type) {
        case 'success':
            messageEl.className = `${baseClasses} bg-green-500 text-white`;
            break;
        case 'error':
            messageEl.className = `${baseClasses} bg-red-500 text-white`;
            break;
        case 'warning':
            messageEl.className = `${baseClasses} bg-yellow-500 text-white`;
            break;
        default:
            messageEl.className = `${baseClasses} bg-blue-500 text-white`;
    }
    
    messageEl.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                <i data-lucide="x" class="w-4 h-4"></i>
            </button>
        </div>
    `;
    
    container.appendChild(messageEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageEl.parentNode) {
            messageEl.style.opacity = '0';
            messageEl.style.transform = 'translateX(100%)';
            setTimeout(() => messageEl.remove(), 300);
        }
    }, 5000);
    
    // Re-initialize icons
    lucide.createIcons();
}

function showError(message) {
    showMessage(message, 'error');
}

function showSuccess(message) {
    showMessage(message, 'success');
}

// User session management
function getCurrentUserId() {
    return localStorage.getItem('user_id');
}

function setCurrentUser(user) {
    localStorage.setItem('user_id', user.user_id);
    localStorage.setItem('user_name', user.name);
    localStorage.setItem('user_email', user.email);
    updateUIWithUser(user);
}

function getCurrentUser() {
    return {
        user_id: localStorage.getItem('user_id'),
        name: localStorage.getItem('user_name'),
        email: localStorage.getItem('user_email')
    };
}

function updateUIWithUser(user) {
    const userInfo = document.getElementById('user-info');
    if (userInfo) {
        userInfo.innerHTML = `
            <span class="text-white">Welcome, ${user.name}</span>
            <button onclick="logout()" class="ml-4 text-white hover:text-gray-200">
                <i data-lucide="log-out" class="w-4 h-4"></i>
            </button>
        `;
    }
    
    // Show/hide login forms
    const loginSection = document.getElementById('login-section');
    const mainContent = document.getElementById('main-content');
    
    if (loginSection && mainContent) {
        loginSection.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }
    
    // Re-initialize icons
    lucide.createIcons();
}

function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    location.reload();
}

// Page-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
    
    // Get current page from URL
    const path = window.location.pathname;
    const page = path.split('/').pop() || 'index';
    
    // Common elements
    const userInfo = document.getElementById('user-info');
    const currentUser = getCurrentUser();
    
    // Check if user is logged in
    if (currentUser.user_id) {
        updateUIWithUser(currentUser);
    }
    
    // Page-specific handlers
    switch(page) {
        case 'train':
        case 'train.html':
            initTrainPage();
            break;
            
        case 'predict':
        case 'predict.html':
            initPredictPage();
            break;
            
        case 'recommend':
        case 'recommend.html':
            initRecommendPage();
            break;
            
        case 'info':
        case 'info.html':
            initInfoPage();
            break;
            
        default:
            initIndexPage();
            break;
    }
});

// Training page functionality
function initTrainPage() {
    const trainForm = document.getElementById('train-form');
    
    if (trainForm) {
        trainForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            showLoading('Training models...');
            
            try {
                const response = await fetch('/api/train', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess(result.message);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showError('Failed to train models: ' + error.message);
            } finally {
                hideLoading();
            }
        });
    }
}

// Prediction page functionality
function initPredictPage() {
    const predictForm = document.getElementById('predict-form');
    
    if (predictForm) {
        predictForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            showLoading('Generating predictions...');
            
            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess(result.message);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showError('Failed to generate predictions: ' + error.message);
            } finally {
                hideLoading();
            }
        });
    }
}

// Recommendation page functionality
function initRecommendPage() {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const recommendForm = document.getElementById('recommend-form');
    
    // Register form handler
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                showLoading('Registering user...');
                
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: formData.get('name'),
                        email: formData.get('email')
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    setCurrentUser(result.user);
                    showSuccess(result.message);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showError('Registration failed: ' + error.message);
            } finally {
                hideLoading();
            }
        });
    }
    
    // Login form handler
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                showLoading('Logging in...');
                
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: formData.get('user_id')
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    setCurrentUser(result.user);
                    showSuccess(result.message);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showError('Login failed: ' + error.message);
            } finally {
                hideLoading();
            }
        });
    }
    
    // Recommendation form handler
    if (recommendForm) {
        recommendForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            // Collect all selected categories
            const categories = [];
            document.querySelectorAll('input[name="categories"]:checked').forEach(checkbox => {
                categories.push(checkbox.value);
            });
            
            // Get category priority from the input field
            const categoryPriorityInput = formData.get('category_priority');
            const categoryPriority = categoryPriorityInput ? 
                categoryPriorityInput.split(',').map(s => s.trim()) : categories;
            
            const requestData = {
                user_id: getCurrentUserId(),
                budget: parseFloat(formData.get('budget')) || 50,
                cuisine: formData.get('cuisine'),
                categories: categories,
                category_priority: categoryPriority,
                require_each_category: formData.get('require_each_category') === 'on',
                time_of_day: formData.get('time_of_day') || 'morning',
                weather: formData.get('weather') || 'sunny'
            };
            
            // Validate inputs
            if (!requestData.cuisine) {
                showError('Please select a cuisine preference');
                return;
            }
            
            if (categories.length === 0) {
                showError('Please select at least one category');
                return;
            }
            
            try {
                showLoading('Getting recommendations...');
                
                const response = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayRecommendations(result.recommendations || [], result.explanations || {}, result.total_cost || 0);
                    showSuccess(result.message);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showError('Failed to get recommendations: ' + error.message);
            } finally {
                hideLoading();
            }
        });
    }
}

// Info page functionality
function initInfoPage() {
    const refreshButton = document.getElementById('refresh-info');
    
    if (refreshButton) {
        refreshButton.addEventListener('click', loadSystemInfo);
    }
    
    // Load info on page load
    loadSystemInfo();
}

function initIndexPage() {
    // No specific initialization needed for index page
}

async function loadSystemInfo() {
    try {
        showLoading('Loading system information...');
        
        const response = await fetch('/api/info');
        const result = await response.json();
        
        if (result.success) {
            displaySystemInfo(result.models);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showError('Failed to load system info: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displaySystemInfo(models) {
    const container = document.getElementById('system-info');
    if (!container) return;
    
    const modelCards = Object.entries(models).map(([name, info]) => `
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold mb-2 capitalize">${name} Model</h3>
            <div class="space-y-2">
                <div class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full mr-2 ${info.exists ? 'bg-green-500' : 'bg-red-500'}"></span>
                    <span class="text-sm">${info.exists ? 'Available' : 'Not found'}</span>
                </div>
                <p class="text-sm text-gray-600">Path: ${info.path}</p>
                ${info.exists ? `<p class="text-sm text-gray-600">Size: ${formatFileSize(info.size)}</p>` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = modelCards;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function displayRecommendations(recommendations, explanations, totalCost) {
    const container = document.getElementById('recommendations-results');
    if (!container) return;
    
    if (recommendations.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <div class="text-gray-500 text-lg">No recommendations found</div>
                <p class="text-gray-400 mt-2">Try adjusting your preferences or budget</p>
            </div>
        `;
        return;
    }
    
    const recommendationCards = recommendations.map((item, index) => `
        <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-lg font-semibold text-gray-800">${item.item_name}</h3>
                    <p class="text-sm text-gray-600">${item.cuisine} • ${item.category}</p>
                </div>
                <div class="text-right">
                    <span class="text-xl font-bold text-green-600">$${item.price.toFixed(2)}</span>
                </div>
            </div>
            
            <div class="mb-4">
                <p class="text-sm text-gray-700">${explanations[item.item_id] || 'Recommended for you'}</p>
            </div>
            
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium text-gray-700">Rate this item:</span>
                    <div class="flex space-x-1" data-item-id="${item.item_id}">
                        ${[1,2,3,4,5].map(rating => `
                            <button onclick="rateItem('${item.item_id}', ${rating})" 
                                    class="text-gray-300 hover:text-yellow-400 transition-colors">
                                <i data-lucide="star" class="w-4 h-4"></i>
                            </button>
                        `).join('')}
                    </div>
                </div>
                <span class="text-xs text-gray-500">ID: ${item.item_id}</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = `
        <div class="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="text-lg font-semibold text-blue-800">Your Recommendations</h3>
                    <p class="text-blue-600">${recommendations.length} items selected</p>
                </div>
                <div class="text-right">
                    <span class="text-sm text-blue-600">Total Cost:</span>
                    <div class="text-2xl font-bold text-blue-800">$${totalCost.toFixed(2)}</div>
                </div>
            </div>
        </div>
        
        <div class="grid gap-6">
            ${recommendationCards}
        </div>
    `;
    
    // Re-initialize icons
    lucide.createIcons();
}

async function rateItem(itemId, rating) {
    const userId = getCurrentUserId();
    if (!userId) {
        showError('Please login to rate items');
        return;
    }
    
    try {
        const response = await fetch('/api/rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                item_id: itemId,
                rating: rating
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('Rating saved successfully');
            
            // Update the star display
            const ratingContainer = document.querySelector(`[data-item-id="${itemId}"]`);
            if (ratingContainer) {
                const stars = ratingContainer.querySelectorAll('button');
                stars.forEach((star, index) => {
                    const starIcon = star.querySelector('i');
                    if (index < rating) {
                        starIcon.classList.remove('text-gray-300');
                        starIcon.classList.add('text-yellow-400');
                    } else {
                        starIcon.classList.remove('text-yellow-400');
                        starIcon.classList.add('text-gray-300');
                    }
                });
            }
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showError('Failed to save rating: ' + error.message);
    }
}
