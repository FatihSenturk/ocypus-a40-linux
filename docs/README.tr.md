# Ocypus Iota A40 — Linux kurulumu

Soğutucunun ekranında işlemci sıcaklığını gösterir. Ubuntu/Debian üzerinde tek
komutla kurulur; işlemci sensörünü otomatik seçer ve bilgisayar açıldığında çalışır.

## Tek komutla kurulum

```bash
curl -fsSL https://raw.githubusercontent.com/FatihSenturk/ocypus-a40-linux/v1.0.0/install.sh | bash
```

İstendiğinde sudo parolanı terminale gir. Kurucu sürümlenmiş kaynak kodunu indirir,
`.deb` paketini oluşturur, gerekli paketleri apt ile kurar ve servisi başlatır.
`curl` yoksa önce `sudo apt install curl` çalıştır.

Alternatif: [Releases sayfasından](https://github.com/FatihSenturk/ocypus-a40-linux/releases/latest)
`ocypus-a40_1.0.0_all.deb` dosyasını indir. İndirdiğin klasörde:

```bash
sudo apt install ./ocypus-a40_1.0.0_all.deb
```

Yerel `.deb` dosyalarını ve bağımlılık kurulumunu destekleyen bir grafik paket
kurucusunda dosyayı açarak da kurabilirsin. Yukarıdaki apt komutu desteklenen yöntemdir.

## Destek ve ayarlar

Fiziksel ekran Ubuntu 24.04 ve AMD işlemciyle doğrulandı. Intel `coretemp` sensörü
de desteklenir; Intel ve Debian üzerinde fiziksel test raporları bekleniyor.
Bu sürüm diğer Ocypus modellerini, birden fazla soğutucuyu veya diğer dağıtımları
desteklediğini iddia etmez. Anakartın dahili USB 2.0 bağlantısı gereklidir.

Varsayılan: otomatik CPU sensörü, °C, saniyede bir güncelleme. Ayarlar
`/etc/default/ocypus-a40` dosyasındadır. Sensör listesini görüntülemek için:

```bash
ocypus-a40 sensors
```

AMD için örnek: `OCYPUS_SENSOR=k10temp`, `OCYPUS_LABEL=Tctl`.
Intel için örnek: `OCYPUS_SENSOR=coretemp`, `OCYPUS_LABEL="Package id 0"`.
Değişiklikten sonra:

```bash
sudo systemctl restart ocypus-a40
```

Ekran en fazla iki basamak gösterir; seçilen birimde 99 üzerindeki değerler 99'a
sınırlandırılır. Bu yüzden °C önerilir. Fahrenheit fiziksel olarak doğrulanmadı.

## Kontrol ve sorun giderme

```bash
ocypus-a40 diagnose
systemctl status ocypus-a40 --no-pager
sudo journalctl -u ocypus-a40 -n 30 --no-pager
```

Ekran boşsa USB bağlantısını ve günlükleri kontrol et. Uyku sonrası servisi yeniden
başlatmayı dene. Aynı ekranı yöneten başka yazılım çalıştırma. Servisin “active”
görünmesi ekranda sayı olduğunu kanıtlamaz; soğutucunun ekranını da kontrol et.

İlk `kur.sh` kurulumundan geçişte eski servis `/var/lib/ocypus-a40/legacy/` içine
yedeklenir. Eski `/opt/ocypus-a40` dosyaları ve elle eklenmiş USB kuralları korunur.

## Kaldırma

```bash
sudo apt remove ocypus-a40
```

Ayarları da kaldırmak için `sudo apt purge ocypus-a40` kullan. Bağımlılıklar ve
ayrılmış sistem kullanıcısı korunur.

## Katkılar

MIT lisanslı topluluk projesidir. USB sürücüsü
[moyunkz'nin projesine](https://github.com/moyunkz/ocypus-a40-digital-linux), ekran
iletişimi [roubilibo'nun düzeltmesine](https://github.com/moyunkz/ocypus-a40-digital-linux/pull/3)
dayanır. Ayrıntılar [NOTICE.md](../NOTICE.md) dosyasındadır.
