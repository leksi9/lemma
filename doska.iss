#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{B3D1F0A2-6C1E-4E57-9C55-6A4D0B7D2F11}
AppName=Доска
AppVersion={#AppVersion}
AppVerName=Доска {#AppVersion}
AppPublisher=Доска репетитора
DefaultDirName={localappdata}\Programs\Doska
DefaultGroupName=Доска
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Doska-Setup
SetupIconFile=doska.ico
UninstallDisplayIcon={app}\Doska.exe
UninstallDisplayName=Доска
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Значки:"

[Files]
Source: "dist\Doska\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\Доска"; Filename: "{app}\Doska.exe"
Name: "{autodesktop}\Доска"; Filename: "{app}\Doska.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Doska.exe"; Description: "Открыть доску"; Flags: nowait postinstall skipifsilent
