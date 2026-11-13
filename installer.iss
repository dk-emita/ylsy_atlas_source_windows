; Optional Inno Setup project. Build dist\ylsy-atlas.exe first.
#define MyAppName "YLSY Atlas"
#define MyAppVersion "4.0.0"
#define MyAppExeName "YLSY Atlas.exe"
#ifndef SourceExe
  #define SourceExe "dist\ylsy-atlas.exe"
#endif
[Setup]
AppId={{94E35865-37F0-4D95-826B-C4753384D30D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Doğukan Düzgün
DefaultDirName={autopf}\YLSY Atlas
DefaultGroupName=YLSY Atlas
OutputDir=dist
OutputBaseFilename=YLSY-Atlas-v4.0.0-Setup
SetupIconFile=assets\atlas-icon.ico
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin
[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "scripts\register_background_sync.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "scripts\unregister_background_sync.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\YLSY Atlas"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\YLSY Atlas"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Ek seçenekler"
[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\register_background_sync.ps1"" -ExePath ""{app}\{#MyAppExeName}"""; Flags: runasoriginaluser waituntilterminated
[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\unregister_background_sync.ps1"""; RunOnceId: "remove-background-sync-task"
[UninstallDelete]
; By default, users' personal records are deliberately preserved.
; Optional secure removal of app data is in [Code].
[Code]
var RemoveUserData: Boolean;
function InitializeUninstall(): Boolean;
var Choice: Integer;
begin
  Choice := MsgBox('Bu bilgisayardaki kişisel üniversite, görev ve belgeler silinsin mi? Google Drive üzerindeki kayıtlar bu işlemle silinmez.' + #13#10 +
    'Evet: Verileriniz silinir. Hayır: Verileriniz daha sonra kullanmak için saklanır.',
    mbConfirmation, MB_YESNOCANCEL);
  if Choice = IDCANCEL then Result := False
  else begin
    RemoveUserData := Choice = IDYES;
    Result := True;
  end;
end;
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var DataFolder: String;
begin
  if (CurUninstallStep = usPostUninstall) and RemoveUserData then begin
    DataFolder := ExpandConstant('{localappdata}\YLSYAtlas2');
    DelTree(DataFolder, True, True, True);
  end;
end;
