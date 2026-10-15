
#!/bin/bash
set -e

# Use an isolated Python virtual environment
python -m venv .build_venv

# Install packages inside the virtual environment
.build_venv/bin/python -m pip install --upgrade pip
.build_venv/bin/python -m pip install -r requirements.txt

# Collect Django static files
.build_venv/bin/python manage.py collectstatic --noinput --settings=config.settings.prod
