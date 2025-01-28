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
    if (editIconUrl) editIconUrl.value = element.dataset.iconUrl || '';
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

// Function to update CSS variables based on settings
function updateSettings(settings) {
    if (!settings || typeof settings.iconSize === 'undefined') {
        console.warn('Invalid settings object:', settings);
        settings = { iconSize: 60 }; // Default fallback
    }

    document.documentElement.style.setProperty('--icon-size', `${settings.iconSize}px`);

    // Determine the number of grid columns based on icon size
    let columns;
    switch (parseInt(settings.iconSize)) {
        case 48:
            columns = 6;
            break;
        case 54:
            columns = 5;
            break;
        case 60:
            columns = 4;
            break;
        default:
            columns = 4;
    }
    document.documentElement.style.setProperty('--grid-columns', columns);
}

// Declare variables at the top level so they're available throughout the module
let iconSizeInputs;
let shortcutUrlInput;

// Function to fetch settings from the backend
async function fetchSettings() {
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) throw new Error('Failed to fetch settings');
        const data = await response.json();
        // Handle both possible response formats
        const settings = data.settings || data;
        updateSettings(settings);

        // Initialize input values based on fetched settings
        if (iconSizeInputs) {
            iconSizeInputs.forEach(input => {
                if (parseInt(input.value) === settings.iconSize) {
                    input.checked = true;
                }
            });
        }
        if (shortcutUrlInput && settings.shortcutUrl) {
            shortcutUrlInput.value = settings.shortcutUrl;
        }
    } catch (error) {
        console.error('Failed to fetch settings:', error);
        // Use default settings on error
        updateSettings({ iconSize: 60 });
    }
}

// Sort apps function
function sortApps(sortBy) {
    const appGrid = document.querySelector('.app-grid');
    const apps = Array.from(appGrid.children);

    apps.sort((a, b) => {
        if (sortBy === 'name') {
            return a.dataset.appName.localeCompare(b.dataset.appName);
        } else if (sortBy === 'category') {
            return a.dataset.category.localeCompare(b.dataset.category);
        } else if (sortBy === 'launchCount') {
            return (parseInt(b.dataset.launchCount) || 0) - (parseInt(a.dataset.launchCount) || 0);
        }
    });

    apps.forEach(app => appGrid.appendChild(app));
}

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize DOM element references first
    iconSizeInputs = document.querySelectorAll('input[name="iconSize"]');
    shortcutUrlInput = document.getElementById('shortcutUrl');

    // Add sort dropdown listeners
    document.querySelectorAll('.dropdown-item[data-sort]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            sortApps(e.target.dataset.sort);
        });
    });

    // Edit mode functionality
    const editModeBtn = document.getElementById('editModeBtn');
    if (editModeBtn) {
        editModeBtn.addEventListener('click', () => {
            document.body.classList.toggle('edit-mode');
            editModeBtn.classList.toggle('active');
        });
    }

    // Handle app clicks
    document.addEventListener('click', async (e) => {
        const appCard = e.target.closest('.app-card');
        if (!appCard) return;

        e.preventDefault();
        e.stopPropagation();

        if (document.body.classList.contains('edit-mode')) {
            editApp(e, appCard);
        } else {
            const appId = appCard.dataset.appId;
            try {
                const response = await fetch(`/api/apps/${appId}/launch`, {
                    method: 'POST'
                });
                if (response.ok) {
                    const data = await response.json();
                    appCard.dataset.launchCount = data.launchCount;
                    launchApp(appCard);
                }
            } catch (error) {
                console.error('Failed to update launch count:', error);
                launchApp(appCard);
            }
        }
    });

    // Then fetch and apply settings
    await fetchSettings();

    // Add event listeners for icon size changes
    iconSizeInputs.forEach(input => {
        input.addEventListener('change', async (e) => {
            const size = parseInt(e.target.value);
            const newSettings = { iconSize: size };

            try {
                const response = await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                if (!response.ok) throw new Error('Failed to save settings');
                const data = await response.json();
                // Handle both possible response formats
                const updatedSettings = data.settings || data;
                updateSettings(updatedSettings);
            } catch (error) {
                console.error('Failed to save settings:', error);
                // Keep the UI consistent with the selected value even if save failed
                updateSettings(newSettings);
            }
        });
    });

    // Add event listener for shortcut URL changes
    if (shortcutUrlInput) {
        shortcutUrlInput.addEventListener('change', async (e) => {
            const newUrl = e.target.value;
            try {
                const response = await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ shortcutUrl: newUrl })
                });
                if (!response.ok) throw new Error('Failed to save shortcut URL');
            } catch (error) {
                console.error('Failed to save shortcut URL:', error);
            }
        });
    }

    const settingsBtn = document.getElementById('settingsBtn');
    const addAppBtn = document.getElementById('addAppBtn');
    const settingsOverlay = document.getElementById('settingsOverlay');
    const editOverlay = document.getElementById('editOverlay');
    const editAppForm = document.getElementById('editAppForm');
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
                category: document.getElementById('editAppCategory')?.value || 'uncategorized',
                iconUrl: document.getElementById('editIconUrl')?.value || '',
                appStoreLink: document.getElementById('editAppStoreLink')?.value || '',
            };

            const isEdit = formData.id && formData.id.length > 0;
            const url = '/api/apps';  // Remove the conditional URL since we're using method to differentiate
            const method = isEdit ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to save app');
                }

                const result = await response.json();
                if (result.status === 'success') {
                    // Refresh the page to show updated data
                    window.location.reload();
                } else {
                    throw new Error(result.error || 'Failed to save app');
                }
            } catch (error) {
                console.error('Failed to save app:', error);
                alert(error.message || 'Failed to save app. Please try again.');
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

    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => console.log('ServiceWorker registration successful'))
            .catch(err => console.log('ServiceWorker registration failed:', err));
    }
});

// Export data
async function exportData() {
    try {
        const response = await fetch('/api/apps');
        const data = await response.json();

        // Create download link with just the apps array
        const blob = new Blob([JSON.stringify(data.apps, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `app-gallery-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Failed to export data:', error);
        alert('Failed to export data');
    }
}

// Import data
async function importData(input) {
    if (!input.files?.length) return;

    try {
        const file = input.files[0];
        const text = await file.text();
        const apps = JSON.parse(text);

        // Check if the imported data is an array (new format) or has an apps property (old format)
        const data = {
            apps: Array.isArray(apps) ? apps : (apps.apps || [])
        };

        if (!Array.isArray(data.apps)) {
            throw new Error('Invalid data format');
        }

        const response = await fetch('/api/apps/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Import failed');

        // Refresh the page to show imported data
        window.location.reload();
    } catch (error) {
        console.error('Failed to import data:', error);
        alert('Failed to import data: ' + error.message);
    } finally {
        input.value = ''; // Reset file input
    }
}

// Fix JSON Structure
async function fixJsonStructure() {
    try {
        const response = await fetch('/api/apps');
        const data = await response.json();
        const apps = data.apps || [];

        // Fix each app's structure
        const fixedApps = apps.map(app => {
            const fixedApp = {
                id: app.id,
                name: app.name,
                category: app.category || 'uncategorized',
                iconUrl: app.iconUrl,
                appStoreLink: app.appStoreLink || app.link || '',
                launchCount: app.launchCount || 0,
                lastModified: app.lastModified || new Date().toISOString(),
                lastLaunched: app.lastLaunched || null
            };
            return fixedApp;
        });

        // Save the fixed structure
        const saveResponse = await fetch('/api/apps/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apps: fixedApps })
        });

        if (!saveResponse.ok) throw new Error('Failed to save fixed structure');

        // Show success message
        alert('JSON structure has been fixed successfully!');

        // Refresh the page to show updated data
        window.location.reload();
    } catch (error) {
        console.error('Failed to fix JSON structure:', error);
        alert('Failed to fix JSON structure: ' + error.message);
    }
}

// Add new category
async function addNewCategory() {
    const newCategoryInput = document.getElementById('newCategory');
    const categorySelect = document.getElementById('editAppCategory');
    if (!newCategoryInput || !categorySelect) {
        console.error('Required elements not found');
        return;
    }

    const category = newCategoryInput.value.trim();
    if (!category) {
        alert('Please enter a category name');
        return;
    }

    try {
        const response = await fetch('/api/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: category })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add category');
        }
        
        const data = await response.json();
        
        if (data.status === 'exists') {
            // If category exists, just select it
            categorySelect.value = data.category.toLowerCase();
        } else if (data.status === 'success') {
            // Add new option and select it
            const categoryValue = data.category.toLowerCase();
            const option = new Option(category, categoryValue);
            categorySelect.add(option);
            categorySelect.value = categoryValue;
            
            // Also add to the filter dropdown
            const filterSelect = document.getElementById('categoryFilter');
            if (filterSelect) {
                filterSelect.add(new Option(category, categoryValue));
            }
        } else {
            throw new Error('Unexpected response from server');
        }
        
        // Clear the input
        newCategoryInput.value = '';
        
    } catch (error) {
        console.error('Failed to add category:', error);
        alert(error.message || 'Failed to add category. Please try again.');
    }
}
