#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{B3D1F0A2-6C1E-4E57-9C55-6A4D0B7D2F11}
AppName=Лемма
AppVersion={#AppVersion}
AppVerName=Лемма {#AppVersion}
AppPublisher=Лемма
DefaultDirName={localappdata}\Programs\Doska
DefaultGroupName=Лемма
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Lemma-Setup
SetupIconFile=lemma.ico
UninstallDisplayIcon={app}\Lemma.exe
UninstallDisplayName=Лемма
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
Source: "dist\Lemma\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\Doska.exe"
Type: files; Name: "{autoprograms}\Доска.lnk"
Type: files; Name: "{autodesktop}\Доска.lnk"

[Icons]
Name: "{autoprograms}\Лемма"; Filename: "{app}\Lemma.exe"
Name: "{autodesktop}\Лемма"; Filename: "{app}\Lemma.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Lemma.exe"; Description: "Открыть Лемму"; Flags: nowait postinstall skipifsilent
