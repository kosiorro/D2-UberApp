; Inno Setup Script dla D2 UberApp
#define MyAppName "D2 UberApp"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "D2 Community"
#define MyAppURL "https://d2uberappmarket.tw5.org"
#define MyAppExeName "D2UberApp.exe"

[Setup]
AppId={{E8B75F3A-8B29-4B52-9A8E-6A942F99F012}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=D2UberApp_Setup_v{#MyAppVersion}
SetupIconFile=static\images\uberapp.ico
UninstallDisplayIcon={app}\static\images\uberapp.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Dirs]
Name: "{app}\data"; Permissions: users-full
Name: "{app}\data\screenshots"; Permissions: users-full
Name: "{app}\data\previews"; Permissions: users-full

[Files]
Source: "dist\D2UberApp\*"; DestDir: "{app}"; Excludes: "data\companion-settings.json"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\D2UberApp\data\companion-settings.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\static\images\uberapp.ico"
Name: "{autoprograms}\{#MyAppName} (Console Launcher)"; Filename: "{app}\Launch_D2_UberApp.bat"; IconFilename: "{app}\static\images\uberapp.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\static\images\uberapp.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
