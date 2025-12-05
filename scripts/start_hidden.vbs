Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = WshShell.CurrentDirectory & "\.."
WshShell.Run "pythonw serveur.py", 0, False
