# YLSY Atlas v4.0.0 — Windows kaynak kodu

Windows/masaüstü uygulamasının kaynak kodudur. Kurulum dosyaları [YLSY Atlas sürüm deposunda](https://github.com/dk-emita/ylsy_atlas) yayımlanır.

## Google Drive geliştirme ayarı

Kişisel OAuth istemci kimliği ve sırrı bu depodan çıkarılmıştır. `resources/google_oauth_client.json.example` dosyasını `resources/google_oauth_client.json` adıyla kopyalayıp `YOUR_...` alanlarını kendi Google Cloud OAuth istemcinizle değiştirin. Gerçek kimlik bilgilerini Git'e göndermeyin.

Windows 4.0.0 sürümü GitHub Releases üzerinden Windows Setup güncellemesini kontrol eder. Daha yeni bir sürüm bulunursa Güncelle veya Çıkış seçeneği gösterilir; kurulum dosyası indirilip doğrulandıktan sonra çalıştırılır.

## Windows derlemesi

Windows üzerinde Python ve Inno Setup 6 kurulu olmalıdır. PowerShell'de proje klasöründen `./build_installer.ps1` çalıştırın. Çıktı yalnızca `dist/YLSY-Atlas-v4.0.0-Setup.exe` dosyasıdır; ara EXE ve derleme dosyaları paketlemenin sonunda temizlenir.

Ara EXE'yi incelemek için `./build.ps1 -Stage` kullanılabilir. Onaylanan paket Python 3.15.0, PySide6 6.12.0 ve PyInstaller 6.22.3 ile derlendi.

Derleme, gerçek uygulama arayüzünü ayrı ve boş bir geçici çalışma alanında açar. Kontrol paneli, JavaScript, CSS, yerel API ve menüler yüklenmeden doğrulama başarılı sayılmaz. Bu kontrol kişisel çalışma verilerini veya bağlı Google Drive hesabını kullanmaz.

## 13 Kasım 2026 masaüstü düzeltmesi

- Qt penceresinin ve sayfa motorunun açılmasını engelleyen uyumsuz ICU DLL dosyaları paketten çıkarıldı. Qt ve onun alt süreci Windows'un ICU uygulamasını kullanır.
- Pencere ve görev çubuğu simgesi onaylı `assets/icon.png` kaynağını kullanır. EXE ve kurulum ICO boyutları aynı görselden üretilir.
- Çalışan uygulama ile kurulum kısayollarının Windows görev çubuğu kimlikleri eşleştirildi.
- `scripts/windows.spec` paketleme kurallarını, `scripts/qt_system_runtime.py` gerekli Windows kütüphanesinin yüklenmesini yönetir.

OAuth işlevleri ve yapılandırma alanları kaynak kodda korunur. Bu depoda gerçek yayıncı OAuth kimliği, client secret, kullanıcı oturum bilgisi veya kullanıcı çalışma verisi bulunmaz. Geliştiriciler kendi OAuth yapılandırmalarını oluşturmalıdır.
