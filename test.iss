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
DisableFinishedPage=no
OutputBaseFilename=FixHR_FaceAttendance_Installer_x64
SolidCompression=yes
WizardStyle=modern
; Installer icon - requires .ico format
; Convert fix_hr_prod_logo.png to .ico using: 
; Online: https://convertio.co/png-ico/ or https://www.icoconverter.com/
; Or ImageMagick: magick convert fix_hr_prod_logo.png -define icon:auto-resize=256,128,64,48,32,16 fix_hr_prod_logo.ico
#ifexist "fix_hr_prod_logo.ico"
SetupIconFile=fix_hr_prod_logo.ico
#else
; ICO file not found - installer will use default icon. Please create fix_hr_prod_logo.ico from PNG file.
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\data"
Name: "{app}\data\profile_images"

[Files]
; App executable built by PyInstaller (one-directory build)
Source: "dist\FixHR_FaceAttendance_x64\FixHR_FaceAttendance_x64.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "dist\FixHR_FaceAttendance_x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Static assets required at runtime
Source: "background-img.jpg"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "fix_hr_prod_logo.png"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "liveness_model.tflite"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Optional runtime data (ship if present)
Source: "dist\FixHR_FaceAttendance_x64\employees.db"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\FixHR_FaceAttendance_x64\face_index.faiss"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\FixHR_FaceAttendance_x64\face_codes.txt"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\FixHR_FaceAttendance_x64\face_index.sig"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\FixHR_FaceAttendance_x64\profile_images\*"; DestDir: "{app}\data\profile_images"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist

; Copy app icon for shortcuts if present
Source: "fix_hr_prod_logo.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Use the executable's icon if .ico file is not available, or specify the .ico file
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  FinishedPage: TWizardPage;

procedure InitializeWizard();
begin
  // Ensure finish page is properly initialized
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Installation completed successfully
    // The finish page will be shown automatically
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Ensure the finish page is shown properly and doesn't close automatically
  if CurPageID = wpFinished then
  begin
    // Finish page is displayed - user must click Finish to close
    WizardForm.NextButton.Caption := 'Finish';
    WizardForm.CancelButton.Visible := False;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;