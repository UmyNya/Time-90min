@echo off
rem 用于快速启动 main.py，不过会弹出 cmd 窗口

rem 设置CMD为UTF-8编码，以解决 py 脚本输出 UTF-8 信息乱码的问题
chcp 65001 > nul
rem 'chcp 65001' 将命令行编码设置为UTF-8。'> nul' 隐藏了命令本身的输出。

rem 设置Python解释器的完整路径
set PYTHON_EXE="C:\Users\Fenrir\AppData\Local\Microsoft\WindowsApps\python3.9.exe"

rem 设置要运行的Python脚本的完整路径
set PYTHON_SCRIPT="E:\time_90min\Time-90min-0.3\main.py"

rem 切换到Python脚本所在的目录 (可选，但推荐，以确保脚本能正确处理相对路径)
cd /d "E:\time_90min\Time-90min-0.3"

rem 运行Python脚本
%PYTHON_EXE% %PYTHON_SCRIPT% %*

rem %* 会将所有传递给此批处理文件的参数转发给Python脚本
rem 例如：my_script.bat --arg1 value1

rem 检查Python脚本的退出状态
if %errorlevel% neq 0 (
    echo.
    echo 错误: Python 脚本执行失败，退出码: %errorlevel%
    pause
) else (
    echo.
    echo Python 脚本成功执行。
)

rem 如果不希望窗口自动关闭，可以暂停窗口(可以用于debug)
rem pause

exit /b %errorlevel%