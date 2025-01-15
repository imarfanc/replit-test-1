document.addEventListener('DOMContentLoaded', function() {
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsOverlay = document.getElementById('settingsOverlay');
    const editOverlay = document.getElementById('editOverlay');
    const iconSizeSelect = document.getElementById('iconSize');
    const appGrid = document.querySelector('.app-grid');

    function updateIconSize(size) {
        document.documentElement.style.setProperty('--icon-size', `${size}px`);
    }

    function showOverlay(overlay) {
        overlay.style.display = 'flex';
    }

    function hideOverlay(overlay) {
        overlay.style.display = 'none';
    }

    settingsBtn?.addEventListener('click', () => showOverlay(settingsOverlay));

    document.querySelectorAll('.overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                hideOverlay(overlay);
            }
        });
    });

    iconSizeSelect?.addEventListener('change', async (e) => {
        const size = e.target.value;
        updateIconSize(size);
        
        try {
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ iconSize: parseInt(size) })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update settings');
            }
        } catch (error) {
            console.error('Error updating settings:', error);
        }
    });

    document.querySelectorAll('.app-card').forEach(card => {
        card.addEventListener('click', () => {
            const appStoreLink = card.dataset.appStoreLink;
            if (appStoreLink) {
                window.location.href = appStoreLink;
            }
        });
    });

    // Initialize icon size from settings
    const currentIconSize = iconSizeSelect?.value || 60;
    updateIconSize(currentIconSize);
});
