# Android 2.4.1

- Native Android WebView shell runs the shared local Python/SQLite backend through Chaquopy.
- Google Drive OAuth/PKCE remains on the existing account flow; Android stores credentials encrypted using Android Keystore.
- Mobile layout uses a centered 95vw work area, Android system safe areas and theme-matched system bars.
- Android back closes the drawer and then navigates through page history. Left-edge swipe opens the drawer with eased motion.
- Automatic online detection and the same local FIFO offline sync journal are included.
