[Setup]
AppId={{B4D5F351-804F-4972-8B47-4A3D65E2F9A8}
AppName=EuroJackpot Reliability Engine
AppVersion=3.8
DefaultDirName={localappdata}\EuroJackpotEngine
DefaultGroupName=EuroJackpot Reliability Engine
OutputDir=installer-output
OutputBaseFilename=EuroJackpotEngine_v3_8_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=EuroJackpot_Desktop_Icon.ico
UninstallDisplayIcon={app}\EuroJackpotEngine.exe

[Files]
Source: "dist\EuroJackpotEngine.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\EuroJackpot Reliability Engine"; Filename: "{app}\EuroJackpotEngine.exe"
Name: "{autodesktop}\EuroJackpot Reliability Engine"; Filename: "{app}\EuroJackpotEngine.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
