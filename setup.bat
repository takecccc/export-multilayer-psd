@echo off

set PYTHONBIN=
call :SET_PYTHONBIN
if "%PYTHONBIN%" == "" (
echo Could not find python binary for Substance 3D Painter.
echo Set PYTHONBIN manually.
exit /b
)

"%PYTHONBIN%" -m pip install -r requirements.txt
:END
pause
exit /b

:SET_PYTHONBIN
set "PYTHONBIN_ADOBE=C:\Program Files\Adobe\Adobe Substance 3D Painter\resources\pythonsdk\python.exe"
set "PYTHONBIN_STEAM=C:\Program Files (x86)\Steam\steamapps\common\Substance 3D Painter 2024\resources\pythonsdk\python.exe"

if exist "%PYTHONBIN_ADOBE%" (
set "PYTHONBIN=%PYTHONBIN_ADOBE%"
exit /b
) 
if exist "%PYTHONBIN_STEAM%" (
set "PYTHONBIN=%PYTHONBIN_STEAM%"
exit /b
)
exit /b
