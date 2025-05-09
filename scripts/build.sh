#!/bin/bash

# Функция для проверки и создания виртуального окружения
setup_venv() {
    # Проверка доступности Python и модуля venv
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Python3 is not installed. Please install it (e.g., 'apt install python3')."
        exit 1
    fi
    if ! python3 -m venv --help >/dev/null 2>&1; then
        echo "python3-venv is not installed. Please install it with 'apt install python3.12-venv' (or the appropriate version for your Python)."
        echo "You may need to use sudo. After installation, rerun this script."
        exit 1
    fi

    # Проверка версии Python
    PYTHON_VERSION=$(python3 --version)
    echo "Using Python version: $PYTHON_VERSION"

    # Удаляем старую директорию venv, если она некорректна
    if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
        echo "Found an invalid virtual environment. Removing it..."
        rm -rf venv
    fi

    # Создаём виртуальное окружение, если его нет
    if [ ! -d "venv" ]; then
        echo "Virtual environment not found. Creating it..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo "Failed to create virtual environment. Check Python installation."
            echo "Try installing python3-full (e.g., 'apt install python3-full')."
            exit 1
        fi
        echo "Virtual environment created successfully."
    fi

    # Проверка наличия activate скрипта
    if [ ! -f "venv/bin/activate" ]; then
        echo "Virtual environment is corrupted: venv/bin/activate not found."
        echo "Removing corrupted venv and retrying..."
        rm -rf venv
        python3 -m venv venv
        if [ $? -ne 0 ] || [ ! -f "venv/bin/activate" ]; then
            echo "Failed to create a valid virtual environment. Please check Python installation."
            exit 1
        fi
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "Failed to activate virtual environment. Check the venv directory."
        exit 1
    fi
}

# Установка зависимостей Python
install_python_deps() {
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Failed to install Python dependencies. Check requirements.txt and internet connection."
        return 1
    fi
    return 0
}

# Сборка Java-проекта
build_java() {
    echo "Building the Java project..."
    mvn clean install -X
    if [ $? -ne 0 ]; then
        echo "Java build failed. Check the errors above."
        return 1
    fi
    return 0
}

# Основной процесс
setup_venv
if install_python_deps; then
    if build_java; then
        echo "Build process completed successfully."
    else
        echo "Build process failed."
    fi
else
    echo "Build process failed due to Python dependencies issue."
fi

# Деактивация виртуального окружения только если оно активно
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi