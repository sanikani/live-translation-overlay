@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [오류] Python 가상환경을 찾을 수 없습니다.
    echo docs\SETUP.md를 참고해 먼저 설치를 완료해 주세요.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [오류] .env 파일이 없습니다.
    echo .env.example을 복사하여 .env를 만들고 Azure Speech Key와 Region을 입력해 주세요.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo 프로그램 실행 중 오류가 발생했습니다.
    pause
)

endlocal
