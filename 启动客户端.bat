@echo off
chcp 65001 >nul
echo ==================================================
echo 智能记账客户端启动器
echo ==================================================
echo.

echo 正在启动服务器...
start /min python simple_desktop_client.py

echo 等待服务器启动...
timeout /t 5 /nobreak >nul

echo 正在启动桌面客户端...
python desktop_client.py

echo.
echo 客户端已启动完成！
pause
