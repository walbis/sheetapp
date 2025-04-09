@echo off
title Create Django-React Project Structure

echo Creating project root folder...
mkdir django-react-sheetapp > nul 2>&1
cd django-react-sheetapp

echo Creating main directories (backend, frontend, k8s)...
mkdir backend > nul 2>&1
mkdir frontend > nul 2>&1
mkdir k8s > nul 2>&1

echo Creating backend structure...
mkdir backend\app > nul 2>&1
mkdir backend\app\migrations > nul 2>&1
mkdir backend\app\models > nul 2>&1
mkdir backend\app\serializers > nul 2>&1
mkdir backend\app\views > nul 2>&1
mkdir backend\app\tests > nul 2>&1
mkdir backend\project_config > nul 2>&1

echo Creating frontend structure...
mkdir frontend\public > nul 2>&1
mkdir frontend\src > nul 2>&1
mkdir frontend\src\assets > nul 2>&1
mkdir frontend\src\assets\fonts > nul 2>&1
mkdir frontend\src\assets\images > nul 2>&1
mkdir frontend\src\components > nul 2>&1
mkdir frontend\src\components\auth > nul 2>&1
mkdir frontend\src\components\common > nul 2>&1
mkdir frontend\src\components\layout > nul 2>&1
mkdir frontend\src\components\modals > nul 2>&1
mkdir frontend\src\components\table > nul 2>&1
mkdir frontend\src\contexts > nul 2>&1
mkdir frontend\src\hooks > nul 2>&1
mkdir frontend\src\pages > nul 2>&1
mkdir frontend\src\services > nul 2>&1
mkdir frontend\src\styles > nul 2>&1
mkdir frontend\src\utils > nul 2>&1

echo.
echo Folder structure created successfully within 'django-react-sheetapp'!
echo You may need to create __init__.py files in Python directories manually.
echo.
pause