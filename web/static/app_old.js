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
