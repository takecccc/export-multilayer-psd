@echo off

set PYTHONBIN=
call :SET_PYTHONBIN
if "%PYTHONBIN%" == "" (
echo Could not find python binary for Substance 3D Painter.
echo Set PYTHONBIN manually.
exit /b
)

set "MODULE_DIR=%~dp0\..\..\modules"
set "PYTHONPATH=%MODULE_DIR%"

"%PYTHONBIN%" -m pip install --upgrade -r requirements.txt -t "%MODULE_DIR%"
"%MODULE_DIR%\bin\cythonize.exe" -i "%MODULE_DIR%\pytoshop\packbits.pyx"
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
