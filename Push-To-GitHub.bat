@echo off
chcp 65001 >nul
color 0A
title 🚀 Push Hugo Posts to GitHub

echo ===================================================
echo     🚀 Hugo Site - Push to GitHub Pages
echo ===================================================
echo.
echo 📁 Directory: P:\HUGO\my-site
echo.

:: Change to the Hugo directory
cd /d P:\HUGO\my-site

:: Show files that will be added
echo 📝 Files modified:
git status -s
echo.

:: Ask for commit message
set /p commitMsg="💬 Enter commit message (or press Enter for 'Update posts'): "
if "%commitMsg%"=="" set commitMsg=Update posts

echo.
echo ⏳ [1/3] Adding changes...
git add .

echo ⏳ [2/3] Committing changes...
git commit -m "%commitMsg%"

echo ⏳ [3/3] Pushing to GitHub...
git push

echo.
echo ===================================================
echo     ✅ Push Complete! Your site is updating.
echo ===================================================
echo.
pause
