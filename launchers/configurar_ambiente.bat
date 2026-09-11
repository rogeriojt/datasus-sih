@echo off
setlocal
cd /d "%~dp0.."
title DATASUS SIH - Configurar ambiente
where wsl >nul 2>nul
if errorlevel 1 (
    echo Este Windows nao tem WSL instalado. Instale com: wsl --install -d Ubuntu
    pause
    exit /b 1
)
for %%A in (".") do set "SHORTPATH=%%~sA"
for /f "delims=" %%p in ('wsl wslpath -a "%SHORTPATH%" 2^>nul') do set WSLPATH=%%p
wsl bash -lc "cd \"%WSLPATH%\" && bash launchers/configurar_ambiente.command"
pause
