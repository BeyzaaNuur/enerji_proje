# Türkiye Enerji İthalatı - Tedarikçi Ülke Bağımlılığı Analizi

Türkiye'nin 1980-2024 yılları arasındaki kömür, petrol gazı (LNG + boru gazı) ve rafine petrol ürünleri ithalatını; tedarikçi ülke bazında yoğunlaşma riskini (HHI, risk skoru), Rusya'ya bağımlılığın zaman içindeki artışını ve bu bağımlılığın cari açığa etkisini inceleyen uçtan uca bir veri analizi projesi.

Proje; ham veri çekme scriptlerinden, temizlenmiş veri setlerinden, risk skorlama modelinden ve bulguları görselleştiren bir Power BI dashboard'undan oluşuyor.

## Dashboard Ekran Görüntüleri

### Genel Bakış
![Genel Bakış](<img width="1319" height="741" alt="Screenshot 2026-10-31 151543" src="https://github.com/user-attachments/assets/c7c70079-6d98-4615-bedd-75f556c7b665" />
)

### Kömür-Rusya Bulgusu: Tek Kaynak Riski Hızla Artıyor
![Kömür-Rusya Bulgusu](screenshots/komur_rusya_bulgusu.png)

### Tedarikçi Riski & Ağ: Rusya'nın Çok Kategorili Sistemik Etkisi
![Tedarikçi Riski ve Ağ](screenshots/tedarikci_riski_ag.png)

### Fiyat Bağlantısı: Küresel Kömür Fiyatları ve Türkiye'nin İthalat Maliyeti
![Fiyat Bağlantısı](screenshots/fiyat_baglantisi.png)

### Rezerv ve Üretim: Türkiye'nin Yerli Kaynakları ve Küresel Kıyaslama
![Rezerv ve Üretim](screenshots/rezerv_ve_uretim.png)

### Ekonomik Etki: Enerji İthalatının Cari Açığa Etkisi
![Ekonomik Etki](screenshots/ekonomik_etki.png)

## Öne Çıkan Bulgular

- Rusya'nın kömür ithalatındaki payı 2015'te %38,4 iken 2023'te %61,9'a yükseldi.
- Rusya; kömür, petrol gazı (LNG + boru gazı) ve rafine petrol ürünleri kategorilerinin tamamında sistemik tedarikçi konumunda (3 kategoride de aktif, toplam $38,6bn tedarik hacmi).
- 2023 itibarıyla toplam enerji ithalatı $424bn, Rusya'nın payı %34,8.
- 2023'te net enerji ithalat bağımlılığı cari açığın %72'sini açıklıyor; enerji hariç cari denge pozitifken enerji ithalatı toplam dengeyi negatife çeviriyor.

## Proje Yapısı

| Dosya | Açıklama |
|---|---|
| `enerji_veri_cek.py`, `enerji_veri_cek_coklu_yil.py`, `enerji_veri_cek_kiyaslama.py` | Enerji ithalat verisini kaynağından çeken scriptler |
| `fiyat_verisi_cek.py` | Küresel emtia fiyat verisini çeken script |
| `rezerv_uretim_verisi_cek.py` | Rezerv/üretim verisini çeken script |
| `risk_skorlama_ag.py`, `risk_skoru_kendi_yazdigim.py` | Tedarikçi yoğunlaşma riski (HHI, risk skoru) hesaplama scriptleri |
| `turkiye_enerji_ithalati_*.csv`, `kiyaslama_ulkeleri_komur.csv`, `kuresel_*.csv`, `tedarikci_merkezilik_2023.csv`, `risk_skorlari_*.csv`, `tcmb_cari_denge_enerji.csv` | Temizlenmiş / işlenmiş veri setleri |
| `EI-Stats-Review-ALL-data.xlsx`, `pink_sheet_ham.xlsx` | Ham kaynak veri dosyaları |
| `enerji_tema.json`, `Atesli_Okyanus_PowerBI_Tema.json` | Dashboard için özel Power BI tema dosyaları |
| `validate_palette.js` | Renk paletinin erişilebilirlik (CVD-safe) doğrulama scripti |
| `dashboard_yapim_rehberi.md`, `bulgular_komur_rusya.md` | Dashboard kurulum notları ve bulgu özetleri |
| `Enerji_Proje_Ara_Bulgular_Raporu.docx` | Ara bulgular raporu |

## Kullanılan Teknolojiler

- **Python** — veri çekme, temizleme ve risk skorlama
- **Power BI Desktop** — dashboard ve görselleştirme
- **JavaScript (Node.js)** — renk paleti doğrulama

## Veri Kapsamı

1980-2024 yılları arasında Türkiye'nin kömür, petrol gazı (LNG + boru gazı) ve rafine petrol ürünleri ithalatı; tedarikçi ülke, kategori ve yıl kırılımında.
