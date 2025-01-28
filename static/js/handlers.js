// Event handlers and form functionality

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

    try {
        await fetch(`/api/apps/${appId}/launch`, { method: 'POST' });
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

    if (launchCountDisplay) {
        const launchCount = element.dataset.launchCount || '0';
        const lastLaunched = element.dataset.lastLaunched ?
            new Date(element.dataset.lastLaunched).toLocaleDateString() : 'Never';
        launchCountDisplay.textContent = `Launched ${launchCount} times • Last: ${lastLaunched}`;
    }

    editOverlay.style.display = 'flex';
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
        console.log('Adding new category:', category); // Debug log
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
        console.log('Server response:', data); // Debug log
        
        if (data.status === 'exists') {
            console.log('Category exists, selecting:', data.category); // Debug log
            categorySelect.value = data.category.toLowerCase();
        } else if (data.status === 'success') {
            console.log('Adding new category to select:', data.category); // Debug log
            const categoryValue = data.category.toLowerCase();
            // Check if option already exists
            let option = Array.from(categorySelect.options).find(opt => opt.value === categoryValue);
            if (!option) {
                option = new Option(category, categoryValue);
                categorySelect.add(option);
            }
            categorySelect.value = categoryValue;
            
            const filterSelect = document.getElementById('categoryFilter');
            if (filterSelect) {
                // Check if option already exists in filter select
                let filterOption = Array.from(filterSelect.options).find(opt => opt.value === categoryValue);
                if (!filterOption) {
                    filterOption = new Option(category, categoryValue);
                    filterSelect.add(filterOption);
                }
            }
        } else {
            throw new Error('Unexpected response from server');
        }
        
        newCategoryInput.value = '';
        return true;
    } catch (error) {
        console.error('Failed to add category:', error);
        alert(error.message || 'Failed to add category. Please try again.');
        return false;
    }
}

// Import data
async function importData(input) {
    if (!input.files || !input.files[0]) return;
    
    try {
        const file = input.files[0];
        const text = await file.text();
        const data = JSON.parse(text);
        
        const response = await fetch('/api/apps/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to import data');
        }
        
        const result = await response.json();
        console.log('Import result:', result);
        
        if (result.status === 'success') {
            alert(`Successfully imported ${result.imported} apps and updated ${result.updated} apps.`);
            window.location.reload();
        } else {
            throw new Error(result.error || 'Failed to import data');
        }
    } catch (error) {
        console.error('Import error:', error);
        alert(error.message || 'Failed to import data. Please check the file format and try again.');
    }
    
    // Clear the input
    input.value = '';
}

// Export data
async function exportData() {
    try {
        const response = await fetch('/api/apps');
        if (!response.ok) throw new Error('Failed to fetch apps');
        
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `app_gallery_export_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export error:', error);
        alert(error.message || 'Failed to export data. Please try again.');
    }
}

// Initialize event handlers
document.addEventListener('DOMContentLoaded', () => {
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
            
            // Check for new category first
            const newCategory = document.getElementById('newCategory')?.value?.trim();
            const editAppCategory = document.getElementById('editAppCategory');
            
            if (newCategory && editAppCategory) {
                // Add the new category first
                const success = await addNewCategory();
                if (!success) {
                    // If adding category failed, don't proceed with form submission
                    return;
                }
                // The addNewCategory function will update the select value if successful
            }
            
            const formData = {
                id: document.getElementById('editAppId')?.value,
                name: document.getElementById('editAppName')?.value,
                category: document.getElementById('editAppCategory')?.value || 'uncategorized',
                iconUrl: document.getElementById('editIconUrl')?.value || '',
                appStoreLink: document.getElementById('editAppStoreLink')?.value || '',
            };

            console.log('Submitting form data:', formData); // Debug log

            const isEdit = formData.id && formData.id.length > 0;
            const url = '/api/apps';
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
                console.log('Server response:', result); // Debug log

                if (result.status === 'success') {
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
}); 