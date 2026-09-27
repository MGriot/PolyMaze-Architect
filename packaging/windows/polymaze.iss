; Windows installer for PolyMaze Architect (Inno Setup 6).
; Build the PyInstaller bundle first, then from the repo root:
;     iscc /DAppVersion=2.0.0 packaging\windows\polymaze.iss
; Output: dist\installer\PolyMazeArchitect-Setup-<version>.exe

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#define AppName "PolyMaze Architect"
#define AppExe "PolyMazeArchitect.exe"
#define Root "..\.."

[Setup]
AppId={{8C1B2D4E-5F6A-4B7C-9D8E-2A3B4C5D6E7F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=PolyMaze Architect
DefaultDirName={autopf}\PolyMaze Architect
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
SetupIconFile={#Root}\src\polymaze\assets\icon.ico
OutputDir={#Root}\dist\installer
OutputBaseFilename=PolyMazeArchitect-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user install by default (no admin prompt); users can still choose all users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Root}\dist\PolyMazeArchitect\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Saves live in %APPDATA%\polymaze and are intentionally kept on uninstall.
