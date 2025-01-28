// Core application functionality
let iconSizeInputs;
let shortcutUrlInput;

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
        case 48: columns = 6; break;
        case 54: columns = 5; break;
        case 60: columns = 4; break;
        default: columns = 4;
    }
    document.documentElement.style.setProperty('--grid-columns', columns);
}

// Function to fetch settings from the backend
async function fetchSettings() {
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) throw new Error('Failed to fetch settings');
        const data = await response.json();
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

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize DOM element references
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

    // Initialize settings
    await fetchSettings();

    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => console.log('ServiceWorker registration successful'))
            .catch(err => console.log('ServiceWorker registration failed:', err));
    }
}); 