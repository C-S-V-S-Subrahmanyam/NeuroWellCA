"""
NeuroWell-CA Backend Application Entry Point
"""
import os
from app import create_app

# Get configuration from environment
config_name = os.getenv('FLASK_ENV', 'development')

# Create app instance
app = create_app(config_name)

if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True if config_name == 'development' else False
    )
