#define SourceExe "..\\output\\MayanMiner.exe"
#define SourceIcon "..\\assets\\logo.ico"

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
SetupIconFile={#SourceIcon}
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

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\MayanMiner');
    if DirExists(DataDir) then
    begin
      if MsgBox('Do you also want to remove your saved Mayan Miner settings, wallet, and downloaded miner (stored in ' + DataDir + ')?', mbConfirmation, MB_YESNO) = IDYES then
        DelTree(DataDir, True, True, True);
    end;
  end;
end;
