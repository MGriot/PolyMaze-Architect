; Windows installer for PolyMaze Architect (Inno Setup 6).
; Build the PyInstaller bundle first, then from the repo root:
;     iscc /DAppVersion=2.0.0 packaging\windows\polymaze.iss
; or run tools\build_windows.ps1, which does both and reads the version from src\polymaze\__init__.py.
; Output: dist\installer\PolyMazeArchitect-Setup-<version>.exe

#ifndef AppVersion
  #error Pass the version: iscc /DAppVersion=x.y.z packaging\windows\polymaze.iss
#endif
#define AppName "PolyMaze Architect"
#define AppExe "PolyMazeArchitect.exe"
#define AppUrl "https://github.com/MGriot/PolyMaze-Architect"
#define Root "..\.."

[Setup]
; Never change AppId: upgrades find the previous install through it.
AppId={{8C1B2D4E-5F6A-4B7C-9D8E-2A3B4C5D6E7F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=MGriot
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName} Setup
DefaultDirName={autopf}\PolyMaze Architect
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayName={#AppName}
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
; Close a running copy before upgrading files in place.
CloseApplications=force

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; Upgrades replace the whole bundle so files dropped from a newer build don't linger.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#Root}\dist\PolyMazeArchitect\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Saves live in %APPDATA%\polymaze and are intentionally kept on uninstall.
