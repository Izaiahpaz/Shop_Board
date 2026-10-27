@echo off
rem Double-click to start the Shop Board. Set DEFAULT_FOLDER in config.py first
rem (or put the folder path after shop_board.py below, in quotes).
cd /d "%~dp0"
python shop_board.py
pause
