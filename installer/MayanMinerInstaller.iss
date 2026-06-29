#define SourceExe "..\\output\\MayanMiner.exe"

[Setup]
AppName=Mayan Miner
AppVersion=1.0.0
AppId={{3F2504E0-4F89-11D3-9A0C-0305E82C3301}}
Publisher=Mayan Miner Open Source
DefaultDirName={pf}\Mayan Miner
DefaultGroupName=Mayan Miner
OutputBaseFilename=MayanMinerSetup
OutputDir=..\output
Compression=lzma
SolidCompression=yes
DisableStartupPrompt=yes
UninstallDisplayIcon={app}\MayanMiner.exe
Uninstallable=yes
ModifyPath=yes
CreateAppDir=yes
DisableProgramGroupPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "MayanMiner.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\Mayan Miner"; Filename: "{app}\MayanMiner.exe"
Name: "{commondesktop}\Mayan Miner"; Filename: "{app}\MayanMiner.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\MayanMiner.exe"; Description: "Launch Mayan Miner"; Flags: nowait postinstall skipifsilent
