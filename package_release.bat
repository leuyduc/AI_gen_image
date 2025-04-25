@echo off
echo Packaging AI Image Generator for release...

:: Create release directory
if not exist release (
    mkdir release
) else (
    echo Cleaning previous release...
    rmdir /s /q release
    mkdir release
)

:: Copy files to release directory
echo Copying files to release directory...
copy dist\AIImageGenerator.exe release\
copy INSTRUCTIONS.txt release\
copy env.example release\.env.example
copy README_NEW.md release\README.md

:: Create sample.env file
echo Creating sample .env file...
echo AI_API_KEY=AIzaSyCuPZxa5XGji6l2yhKOwmv3ZRMRqNWgHgA > release\.env
echo API_PROVIDER=gemini >> release\.env
echo DARK_MODE=1 >> release\.env

echo Release package created successfully.
echo The release files are in the 'release' directory.
pause 