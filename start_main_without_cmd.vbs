' 以隐藏 cmd 窗口的方式，静默调用 start_main.bat

Set WshShell = CreateObject("WScript.Shell")
' 第一个参数是 BAT 脚本的完整路径
' 第二个参数是窗口样式：0 表示隐藏，1 正常，7 最小化
' 第三个参数是等待完成：True 表示等待 BAT 脚本执行完毕，False 不等待
WshShell.Run "cmd.exe /c ""E:\time_90min\Time-90min-0.3\start_main.bat""", 0, True
' 如果你的BAT脚本需要参数，可以这样传递：
' WshShell.Run "cmd.exe /c ""E:\time_90min\Time-90min-0.3\run_my_python_script.bat param1 param2""", 0, True
' 这里的参数需要手动写死在VBS文件中，或者通过VBScript的命令行参数获取。