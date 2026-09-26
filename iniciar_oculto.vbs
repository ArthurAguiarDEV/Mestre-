' Liga o Mestre sem abrir janela preta (usado no inicio automatico).
Set fso = CreateObject("Scripting.FileSystemObject")
pasta = fso.GetParentFolderName(WScript.ScriptFullName)
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = pasta
shell.Run """" & pasta & "\venv\Scripts\pythonw.exe"" -m app.main", 0, False
