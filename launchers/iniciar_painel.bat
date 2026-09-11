@echo off
setlocal
cd /d "%~dp0.."
title DATASUS SIH - Painel
for %%A in (".") do set "SHORTPATH=%%~sA"
for /f "delims=" %%p in ('wsl wslpath -a "%SHORTPATH%" 2^>nul') do set WSLPATH=%%p
wsl bash -lc "cd \"%WSLPATH%\" && bash launchers/iniciar_painel.command"
pause
