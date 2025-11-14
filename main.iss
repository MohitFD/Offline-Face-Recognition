; =========================
; FixHR Face Attendance Installer (x64)
; =========================

#define MyAppName "FixHR Face Attendance"
#define MyAppVersion "1.0"
#define MyAppPublisher "Fixingdots"
#define MyAppExeName "FixHR_FaceAttendance_x64.exe"

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
OutputBaseFilename=FixHR_FaceAttendance_Installer_x64
SolidCompression=yes
WizardStyle=modern
; Use installer icon only if the file exists to avoid compile aborts
#ifexist "fix_hr_prod_logo.ico"
SetupIconFile=fix_hr_prod_logo.ico
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\data"
Name: "{app}\data\profile_images"

[Files]
; App executable built by PyInstaller (one-file build)
Source: "dist\FixHR_FaceAttendance_x64.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

; Static assets required at runtime
Source: "background-img.jpg"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "fix_hr_prod_logo.png"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "liveness_model.tflite"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Optional runtime data (ship if present)
Source: "dist\main\employees.db"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\main\face_index.faiss"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\main\face_codes.txt"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\main\face_index.sig"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
; If you want to pre-seed images, uncomment the following:
; Source: "dist\main\profile_images\*"; DestDir: "{app}\data\profile_images"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist

; Copy app icon for shortcuts if present
Source: "fix_hr_prod_logo.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Use the provided ICO for shortcuts
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\fix_hr_prod_logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\fix_hr_prod_logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
