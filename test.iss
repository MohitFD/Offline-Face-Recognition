; =========================
; FixHR Face Attendance Installer
; =========================

#define MyAppName "FixHR Face Attendance"
#define MyAppVersion "1.0"
#define MyAppPublisher "Fixingdots"
#define MyAppExeName "FixHr Face Attendance.exe"

[Setup]
AppId={{C3262458-44AA-4C6C-AC93-8A23DB68B86F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
ChangesAssociations=no
DisableProgramGroupPage=no
OutputBaseFilename=FixHR_Installer
SolidCompression=yes
WizardStyle=modern
SetupIconFile=D:\Ml_Projects\Offline-Face-Recognition\fix_hr_prod_logo.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\Ml_Projects\Offline-Face-Recognition\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Ml_Projects\Offline-Face-Recognition\dist\employees.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Ml_Projects\Offline-Face-Recognition\dist\profile_images\*"; DestDir: "{app}\profile_images"; Flags: recursesubdirs createallsubdirs
Source: "D:\Ml_Projects\Offline-Face-Recognition\fix_hr_prod_logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\fix_hr_prod_logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\fix_hr_prod_logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
