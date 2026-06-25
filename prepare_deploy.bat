@echo off
REM ============================================================
REM  LRAT - Prepare for deployment (run this on your laptop)
REM  Builds the React frontend and copies it into backend\static
REM  so the deployed FastAPI server can serve the website.
REM ============================================================

echo.
echo ==^> Building frontend...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo ==^> Copying build into backend\static...
if exist backend\static rmdir /s /q backend\static
mkdir backend\static
xcopy /e /i /y frontend\dist\* backend\static\

echo.
echo ==^> Done! Now commit and push to GitHub:
echo     git add .
echo     git commit -m "Update build"
echo     git push
echo.
pause
