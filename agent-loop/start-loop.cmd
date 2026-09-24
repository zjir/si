@echo off
rem Starts the agent loop. Extra arguments are passed to loop.ps1 (e.g. "start-loop.cmd once").
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0loop.ps1" %*
