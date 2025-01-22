
# iOS App Gallery

A web application to organize and launch iOS apps using custom URLs. Built with Flask and vanilla JavaScript.

## Features

- Display apps in a grid layout with icons and names
- Sort apps by name, category, or launch count
- Edit app details including name, icon URL, and category
- Track app launch counts
- Dark/light theme support
- Responsive design for mobile devices
- PWA support for installation on iOS devices

## Getting Started

1. Clone the repository
2. Run `python main.py`
3. Access the application at `http://0.0.0.0:5000`

## Project Structure

```
├── data/               # JSON data storage
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── icons/        # PWA icons
├── templates/         # HTML templates
└── app.py            # Flask application
```

## API Endpoints

- `GET /api/apps` - Get all apps
- `POST /api/apps` - Create new app
- `PUT /api/apps` - Update app
- `DELETE /api/apps/<app_id>` - Delete app
- `POST /api/apps/<app_id>/launch` - Increment launch count
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## License

MIT
