@echo off
title MCR - Pepe The Black Parade ASCII Animation
cd /d "%~dp0"

set "PY_EXE=C:\Users\Axioo\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if exist "%PY_EXE%" (
    "%PY_EXE%" mcr.py %*
) else (
    python mcr.py %*
)

