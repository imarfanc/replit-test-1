// Get input elements
const iconSizeInputs = document.querySelectorAll('input[name="iconSize"]');
const shortcutUrlInput = document.getElementById('shortcutUrl');

// Load settings
const settings = {
    iconSize: parseInt(localStorage.getItem('iconSize')) || 60,
    shortcutUrl: localStorage.getItem('shortcutUrl') || 'shortcuts://run-shortcut?name=open_iOS_Apps'
};

// Initialize input values
iconSizeInputs.forEach(input => {
    if (parseInt(input.value) === settings.iconSize) {
        input.checked = true;
    }
});
shortcutUrlInput.value = settings.shortcutUrl;

// Update CSS variables and save settings
function updateSettings() {
    document.documentElement.style.setProperty('--icon-size', `${settings.iconSize}px`);
    
    // Set number of columns based on icon size
    let columns;
    switch (settings.iconSize) {
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

// Add event listeners
iconSizeInputs.forEach(input => {
    input.addEventListener('change', (e) => {
        settings.iconSize = parseInt(e.target.value);
        localStorage.setItem('iconSize', settings.iconSize);
        updateSettings();
    });
});

shortcutUrlInput.addEventListener('change', (e) => {
    settings.shortcutUrl = e.target.value;
    localStorage.setItem('shortcutUrl', settings.shortcutUrl);
});

// Initial update
updateSettings(); 