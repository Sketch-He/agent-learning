@echo off
REM Python 安装脚本 —— 自动处理 PATH 问题
REM 双击运行，或终端执行 run_demo.bat

set PYTHON=C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe

if not exist "%PYTHON%" (
    echo Python not found at %PYTHON%
    pause
    exit /b 1
)

"%PYTHON%" demo.py
pause
