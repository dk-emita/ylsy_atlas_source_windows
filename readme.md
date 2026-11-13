# YLSY Atlas Desktop 4.0.0

Windows desktop edition of YLSY Atlas. The desktop interface uses the shared
Atlas workspace and keeps the current local records, guide, document studio,
language tools, calendar, and Google Drive backup features.

## Build

Run `build_installer.ps1` in PowerShell on Windows with Python and Inno Setup 6
installed. The release output is `dist/YLSY-Atlas-v4.0.0-Setup.exe`; intermediate
application binaries and build files are cleaned after packaging.

`build.ps1 -Stage` creates an intermediate EXE for diagnosis. Every build runs
the frozen application's real interface against an isolated temporary workspace
and checks the dashboard, navigation, CSS, JavaScript and local API before the
installer is produced. The check does not use the user's data or Drive account.

## Google Drive

Windows workspace data is stored under `%LOCALAPPDATA%\YLSY Atlas`. Existing
`%LOCALAPPDATA%\YLSYAtlas2` data is moved automatically on first launch when
the destination is empty. If both folders contain data, neither is overwritten.

Windows user data is stored in `%LOCALAPPDATA%\YLSY Atlas`. If an existing
`%LOCALAPPDATA%\YLSYAtlas2` workspace is found, it is moved to the new name on
first launch when the destination is empty. If both locations contain data,
neither is deleted or overwritten.

The bundled configuration uses the existing Google Cloud Desktop OAuth client
and its matching installed-app metadata. Authentication uses the system browser
with PKCE. User refresh credentials are stored in the Windows credential vault.

## Local data

User records are stored in the Windows application data folder. The packaged
application includes the YLSY US graduate application guide and approved Atlas
desktop icon.

## Windows startup and icon fixes — 13 November 2026

The package excludes incompatible third-party ICU DLLs so Qt and its renderer
use the Windows ICU implementation. The Windows window and taskbar use the
approved `assets/icon.png`; shell icons are generated from the same source.
Installer shortcuts carry the same AppUserModelID as the running application.

Public source is maintained in the sibling `ylsy_atlas_source_windows` folder.
Its OAuth configuration is an example with placeholders; this private working
folder's real OAuth file must never be copied into the public source repository.
