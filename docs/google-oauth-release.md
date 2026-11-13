# Google Drive bağlantısını yayımlama

Uygulama, Google Desktop OAuth istemcisi, sistem tarayıcısı, PKCE ve `127.0.0.1` dönüşü kullanır. Kullanıcı yetkilendirdikten sonra Google Drive klasörlerini listeler ve seçilen konumda uygulamaya ait `YLSY Atlas` klasörünü oluşturur veya mevcut olanı kullanır. Kayıtlı erişim belirteçleri Windows kimlik bilgisi kasasında tutulur.

## Google Cloud hazırlığı

1. Google Cloud projesinde **Google Drive API** hizmetini etkinleştirin.
2. OAuth onay ekranında uygulamanın adı, destek e-postası, doğrulanmış alan adı, gizlilik politikası ve veri kullanımı açıklamasını tamamlayın.
3. **Desktop app** türünde OAuth istemcisi oluşturun. Masaüstü akışı PKCE kullanır; `resources/google_oauth_client.json` içinde yalnızca bu istemcinin `client_id` değerini paketleyin. `client_secret` eklemeyin.
4. Geliştirme sırasında OAuth uygulaması Testing durumundaysa test edecek Google hesaplarını test kullanıcılarına ekleyin. Her hesabın uygulama ekranından klasör listeleme ve ilk senkronizasyonu tamamladığını doğrulayın.
5. Halka açık dağıtımdan önce onay ekranını Production durumuna alın ve Google'ın istediği uygulama doğrulamasını tamamlayın. Mevcut klasör gezgini `https://www.googleapis.com/auth/drive` kapsamını istiyor. Google bunu **restricted** olarak sınıflandırıyor; inceleme tamamlanmadan herkese sorunsuz giriş garanti edilemez.
6. Gelecekte Google Picker ve `drive.file` kapsamına geçiş, daha dar izinle klasör seçimi sağlayabilir. Bu geçiş Google Picker yapılandırması ve mevcut kullanıcıların Drive klasörü erişimi için veri geçiş planı gerektirir; yalnızca kapsam metnini değiştirmek mevcut klasör gezginini çalışır bırakmaz.

## Yayın kontrolü

- Yeni bir Google hesabıyla giriş yapın; dönüş sayfasında başarıyı, uygulamada klasör listesini ve seçilen klasörde ilk yedeği doğrulayın.
- Uygulamayı kapatıp açın; kayıtlı oturumla klasörün ve senkronizasyonun sürdüğünü doğrulayın.
- Çevrimdışıyken çalışma kaydedin; ağ gelince Drive yedeğini ve yerel veriyi karşılaştırın.
- Windows EXE ve kurulum paketini temiz bir Windows hesabında deneyin. Kod imzası ve yükleyici güvenilirliği ayrıca yayıncı tarafından yönetilmelidir.

Google'ın masaüstü OAuth akışı tarayıcıya dönülen sayfada kullanıcının sekmeyi kapatıp uygulamaya dönmesini önermektedir. Uygulama `window.close()` dener; kullanıcının normal tarayıcısında açılan sekmeyi tarayıcı kapatmayı engelleyebilir. Başarı göstergesi sekmenin kapanması değil, uygulamada klasör listesinin yüklenmesidir.
