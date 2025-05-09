#!/bin/bash
echo "Running Python scripts..."
# Запускаем database.py (например, для инициализации базы данных)
python3 src/main/python/database.py
# Запускаем API-сервер
python3 src/main/python/api/CallDiagnosis_api.py