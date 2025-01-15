// Handle clipboard paste
async function pasteFromClipboard(targetId) {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.getElementById(targetId);
        if (input) {
            input.value = text;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    } catch (err) {
        console.error('Failed to read clipboard:', err);
    }
}

// Search for app in DuckDuckGo
function searchAppStore() {
    const appName = document.getElementById('editAppName')?.value;
    if (!appName) return;
    
    const query = encodeURIComponent(`${appName} app store ios`);
    window.open(`https://duckduckgo.com/?q=${query}`, '_blank');
}

// Delete app
async function deleteApp() {
    const appId = document.getElementById('editAppId')?.value;
    if (!appId) return;
    
    if (!confirm('Are you sure you want to delete this app?')) return;
    
    try {
        const response = await fetch(`/api/apps/${appId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete app');
        
        // Refresh the page to show updated data
        window.location.reload();
    } catch (error) {
        console.error('Failed to delete app:', error);
    }
}

// Handle app launching with shortcuts
async function launchApp(element) {
    if (!element) return;
    const appName = element.dataset.appName;
    const appId = element.dataset.appId;
    const shortcutUrlInput = document.getElementById('shortcutUrl');
    const shortcutUrl = shortcutUrlInput ? shortcutUrlInput.value : 'shortcuts://run-shortcut?name=open_iOS_Apps';
    const url = `${shortcutUrl}&input=${encodeURIComponent(appName)}`;
    
    // Increment launch count
    try {
        await fetch(`/api/apps/${appId}/launch`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Failed to update launch count:', error);
    }
    
    window.location.href = url;
}

// Handle app editing
function editApp(event, element) {
    if (!element) return;
    event.preventDefault();
    const editOverlay = document.getElementById('editOverlay');
    if (!editOverlay) return;

    const editAppId = document.getElementById('editAppId');
    const editAppName = document.getElementById('editAppName');
    const editAppCategory = document.getElementById('editAppCategory');
    const editIconUrl = document.getElementById('editIconUrl');
    const editAppStoreLink = document.getElementById('editAppStoreLink');
    const editOverlayTitle = document.getElementById('editOverlayTitle');
    const launchCountDisplay = document.getElementById('launchCountDisplay');
    
    editOverlay.dataset.mode = 'edit';
    if (editOverlayTitle) editOverlayTitle.textContent = 'Edit App';
    if (editAppId) editAppId.value = element.dataset.appId || '';
    if (editAppName) editAppName.value = element.dataset.appName || '';
    if (editAppCategory) editAppCategory.value = element.dataset.category || '';
    if (editIconUrl) editIconUrl.value = element.querySelector('img')?.src || '';
    if (editAppStoreLink) editAppStoreLink.value = element.dataset.appStoreLink || '';
    
    // Display launch count if available
    if (launchCountDisplay) {
        const launchCount = element.dataset.launchCount || '0';
        const lastLaunched = element.dataset.lastLaunched ? 
            new Date(element.dataset.lastLaunched).toLocaleDateString() : 'Never';
        launchCountDisplay.textContent = `Launched ${launchCount} times • Last: ${lastLaunched}`;
    }
    
    editOverlay.style.display = 'flex';
}

// Handle settings
document.addEventListener('DOMContentLoaded', () => {
    const settingsBtn = document.getElementById('settingsBtn');
    const addAppBtn = document.getElementById('addAppBtn');
    const settingsOverlay = document.getElementById('settingsOverlay');
    const editOverlay = document.getElementById('editOverlay');
    const editAppForm = document.getElementById('editAppForm');
    const iconSizeInputs = document.querySelectorAll('input[name="iconSize"]');
    const shortcutUrlInput = document.getElementById('shortcutUrl');
    const categoryFilter = document.getElementById('categoryFilter');

    // Show settings
    if (settingsBtn && settingsOverlay) {
        settingsBtn.addEventListener('click', () => {
            settingsOverlay.style.display = 'flex';
        });
    }

    // Show add app overlay
    if (addAppBtn && editOverlay) {
        addAppBtn.addEventListener('click', () => {
            const editAppId = document.getElementById('editAppId');
            const editAppName = document.getElementById('editAppName');
            const editAppCategory = document.getElementById('editAppCategory');
            const editIconUrl = document.getElementById('editIconUrl');
            const editAppStoreLink = document.getElementById('editAppStoreLink');
            const editOverlayTitle = document.getElementById('editOverlayTitle');
            
            editOverlay.dataset.mode = 'add';
            if (editOverlayTitle) editOverlayTitle.textContent = 'Add App';
            if (editAppId) editAppId.value = '';
            if (editAppName) editAppName.value = '';
            if (editAppCategory) editAppCategory.value = '';
            if (editIconUrl) editIconUrl.value = '';
            if (editAppStoreLink) editAppStoreLink.value = '';
            
            editOverlay.style.display = 'flex';
        });
    }

    // Handle form submission
    if (editAppForm) {
        editAppForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = {
                id: document.getElementById('editAppId')?.value,
                name: document.getElementById('editAppName')?.value,
                category: document.getElementById('editAppCategory')?.value,
                iconUrl: document.getElementById('editIconUrl')?.value,
                appStoreLink: document.getElementById('editAppStoreLink')?.value
            };

            try {
                const method = formData.id ? 'PUT' : 'POST';
                const response = await fetch('/api/apps', {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) throw new Error('Failed to save app');
                
                // Refresh the page to show updated data
                window.location.reload();
            } catch (error) {
                console.error('Failed to save app:', error);
            }
        });
    }

    // Handle category filter
    if (categoryFilter) {
        categoryFilter.addEventListener('change', () => {
            const selectedCategory = categoryFilter.value.toLowerCase();
            const apps = document.querySelectorAll('.app-card');
            
            apps.forEach(app => {
                const appCategory = app.dataset.category;
                if (!selectedCategory || appCategory === selectedCategory) {
                    app.style.display = '';
                } else {
                    app.style.display = 'none';
                }
            });
        });
    }

    // Handle icon size change
    iconSizeInputs.forEach(input => {
        input.addEventListener('change', async () => {
            const size = input.value;
            document.documentElement.style.setProperty('--icon-size', `${size}px`);
            
            try {
                await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ iconSize: parseInt(size) })
                });
            } catch (error) {
                console.error('Failed to save settings:', error);
            }
        });
    });

    // Handle shortcut URL change
    if (shortcutUrlInput) {
        let saveTimeout;
        shortcutUrlInput.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(async () => {
                try {
                    await fetch('/api/settings', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ shortcutUrl: shortcutUrlInput.value })
                    });
                } catch (error) {
                    console.error('Failed to save settings:', error);
                }
            }, 500);
        });
    }

    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => console.log('ServiceWorker registration successful'))
            .catch(err => console.log('ServiceWorker registration failed:', err));
    }
});
