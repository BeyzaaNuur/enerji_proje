# Dashboard Yapım Rehberi
### Türkiye'nin Enerji İthalatında Tedarikçi Ülke Bağımlılığı ve Tek-Kaynak Riski Ağı

Bu dosya, Power BI Desktop'ta 6 sayfalık dashboard'u kurarken yanında açık tutup takip edeceğin bir rehber. Her sayfa için: hangi görsel, hangi alanları nereye sürükleyeceğin, hangi filtreyi uygulayacağın ve o sayfada gerçekte ne göreceğin (gerçek verilerle, doğrulama için) yazıyor.

---

## Sayfa 1 — Genel Bakış

**Amaç:** Türkiye'nin enerji ithalatına genel bağımlılığını ve mevcut riskin büyüklüğünü ilk bakışta özetlemek.

1. **Yıl dilimleyici (Slicer):** `Yil_Boyutu[yil]` — sayfanın üstüne, tüm görselleri filtreleyecek şekilde.
2. **4 KPI kartı (Card):**
   - `Ölçüler[Toplam İthalat (USD)]`
   - `Ölçüler[Rusya Payı %]`
   - `Ölçüler[Yüksek Yoğunlaşma Kategori Sayısı]` → 2023'te **3/3**
   - `Ölçüler[Sistemik Tedarikçi Sayısı]` → **29** ülke
3. **Çizgi grafik — Net Enerji İthalatı %:** X ekseni `turkiye_enerji_trend_theglobaleconomy_TR[yil]`, Y ekseni `[net_enerji_ithalati_yuzde]`.
   *Doğrulama:* 2015'te ~%80.4, dalgalanarak 2023'te ~%72.0 — yani Türkiye enerjisinin sürekli %70+'ini dışarıdan alıyor.
4. **Yığılmış çubuk grafik — Kategoriye göre yıllık ithalat:** X `turkiye_enerji_ithalati_coklu_yil[yil]`, Y `ithalat_tutari_usd` (Sum), Legend `kategori`.
   *Doğrulama:* 2023 toplamı ~$73.8 milyar; en büyük dilim Rafine Petrol Ürünleri (~$42.8 milyar).

---

## Sayfa 2 — Kömür-Rusya Bulgusu (ana bulgu)

**Amaç:** Projenin başlık bulgusunu tek sayfada kanıtla: kömürde Rusya bağımlılığı hızla artıyor.

1. **Büyük başlık kartı / metin kutusu:** "2023'te kömür ithalatının %61.9'u tek ülkeden: Rusya"
2. **Çizgi grafik — Rusya'nın kömürdeki payı (2015-2023):** `risk_skorlari_kategori_yil` tablosunu `kategori = "Kömür"` filtrele, X `yil`, Y `top1_payi_yuzde`.
   *Doğrulama (gerçek değerler):* 2015: %38.4 → 2018: %41.3 (o yıl lider Kolombiya) → 2022: %47.7 → **2023: %61.9**. Yani 2023'teki sıçrama gerçek ve keskin.
3. **Çubuk grafik — 2023 kömür tedarikçileri (Top N):** `turkiye_enerji_ithalati_coklu_yil` tablosunu `kategori = Kömür`, `yil = 2023` filtrele, X `ithalat_tutari_usd` (Sum), Y `tedarikci_ulke`, sırala azalan. Görsel filtresinde **Top N = 8** uygula. Rusya çubuğunu vurgulamak için o barın rengini kırmızı yap (koşullu biçimlendirme veya elle).
4. **KPI kartı:** `Ölçüler[Risk Skoru]` (Kömür + 2023 filtreli) → **42.3**, altına `hhi = 0.4233 → "Yüksek Yoğunlaşma"` notu.
5. **(Opsiyonel) Kıyaslama tablosu:** `kiyaslama_ulkeleri_komur` tablosundan `raportor_ulke`, `pay_yuzdesi` (Rusya'nın diğer ülkelerin kömür ithalatındaki payı) — Türkiye'nin bu oranı diğer ülkelerle nasıl kıyaslandığını gösterir.

---

## Sayfa 3 — Tedarikçi Riski & Ağ

**Amaç:** HHI tabanlı risk skorlamasını ve networkx ile kurduğun tedarikçi ağını göstermek.

1. **4 KPI kartı:** `[Ortalama HHI]`, `[Yüksek Yoğunlaşma Kategori Sayısı]`, `[Sistemik Tedarikçi Sayısı]`, `[Toplam Tedarik Hacmi 2023]` (~$73.8 milyar).
2. **Çizgi grafik — Risk Skoru trendi:** X `risk_skorlari_kategori_yil[yil]`, Y `[Risk Skoru]`, Legend `kategori`. 3 çizgi göreceksin.
   *Doğrulama:* Kömür 24.4→42.3, Petrol Gazı 22.6→32.2, Rafine Petrol 12.3→31.9 — **üçü de yükseliyor**, en dikkat çekici olan Rafine Petrol (2021'de %16'dan 2023'te %31.9'a neredeyse ikiye katlandı).
3. **Görsel (Image) — Tedarikçi ağı:** `enerji_tedarik_agi_2023.png` dosyasını ekle (klasöründe hazır).
4. **Tablo — Sistemik tedarikçiler:** `tedarikci_merkezilik_2023` tablosundan `ulke`, `kac_kategoriye_tedarikci`, `kategoriler`, `toplam_hacim_usd`; filtrede `sistemik_tedarikci_mi = True` (29 ülke, en üstte Rusya $38.6 milyar ile 3 kategoride de tedarikçi).

---

## Sayfa 4 — Fiyat Bağlamı

**Amaç:** İthalat maliyetindeki artışın küresel fiyat hareketlerinden mi yoksa bağımlılıktan mı kaynaklandığını ayırt etmek.

1. **Çoklu çizgi grafik:** X `kuresel_enerji_fiyatlari_yillik[yil]`, Y ekseninde birlikte: `komur_fiyati_avustralya_usd_ton`, `dogalgaz_fiyati_avrupa_usd`, `lng_fiyati_japonya_usd` (3 ölçü aynı grafikte, farklı çizgiler).
   *Doğrulama:* 2022'de tüm fiyatlarda keskin zirve — Avustralya kömürü $344.9/ton, Avrupa gazı $40.3, LNG Japonya $18.4 — enerji krizi yılı. 2023'te fiyatlar geriliyor ama hâlâ 2015 seviyesinin üstünde.
2. **KPI kartı:** `Ölçüler[Ort. Kömür Fiyatı (Avustralya)]`.
3. **Yorum kutusu:** 2022 fiyat zirvesiyle Sayfa 1'deki 2022 ithalat harcaması zirvesini ($32.7 milyar kömür) yan yana koy — fiyat artışı ile harcama artışının örtüştüğünü, ama 2023'teki Rusya payı sıçramasının fiyattan değil tedarik yapısından geldiğini vurgula.

---

## Sayfa 5 — Rezerv & Üretim (küresel bağlam)

**Amaç:** Türkiye'nin bağımlı olduğu kaynakların dünya genelinde ne kadar yoğunlaştığını göstermek (arz tarafı).

1. **Dilimleyici:** `kuresel_rezerv_uretim_temiz[metrik]` (örn. kömür rezervi, doğalgaz üretimi vb. — tabloyu açıp gerçek metrik adlarını görüp seçeceksin).
2. **Yatay çubuk grafik — Ülkeye göre dünya payı:** X `dunya_payi_yuzde`, Y `ulke`, azalan sırala, Top N = 10.
3. **Kart:** `deger_sayisal` toplamı veya seçili metrik için Türkiye'nin sırası (varsa).
   *Not:* Bu tablo yıl bazlı değil (tek anlık görünüm), bu yüzden Sayfa 1'deki yıl dilimleyicisi bu sayfayı etkilemeyecek — bu normal.

---

## Sayfa 6 — Ekonomik Etki

**Amaç:** Enerji ithalatının cari açık üzerindeki etkisini göstermek — bağımlılığın makroekonomik faturası.

1. **Kombo grafik (Sütun + Çizgi):** X `tcmb_cari_denge_enerji[yil]`, Sütun `enerji_ithalati_milyon_usd`, Çizgi `cari_islemler_dengesi_milyon_usd`.
   *Doğrulama:* 2022'de enerji ithalatı $96.5 milyara fırlarken cari denge -$46.7 milyara düşüyor — aynı yıl. 2019'da enerji ithalatı düşükken ($41.7 milyar) cari denge pozitife dönüyor (+$15 milyar).
2. **KPI kartı:** `Ölçüler[Toplam Enerji Hariç Cari Denge]` — enerji hariç tutulsaydı Türkiye'nin cari dengesinin ne kadar farklı görüneceğini gösterir.
3. **Yorum kutusu:** "Enerji ithalatı olmasa cari denge kaç yıl pozitif olurdu?" sorusuna görsel üzerinden cevap ver (enerji_haric_cari_denge_milyon_usd sütununu incele — çoğu yıl pozitif çıkıyor, bu da cari açığın büyük kısmının enerji kaynaklı olduğunu gösteriyor).

---

## Genel notlar

- Tüm sayfalarda üstte aynı `Yil_Boyutu[yil]` dilimleyicisini kullan (Sayfa 5 hariç) — tutarlı bir gezinme deneyimi için "Sync slicers" (Dilimleyicileri Senkronize Et) özelliğini açabilirsin (Görünüm sekmesi → Sync slicers).
- Renk paleti önerisi: Rusya'yı her grafikte **aynı kırmızı** ile vurgula (View → Format → Data colors'tan sabitle) — göz, sayfa değiştirse bile aynı ülkeyi takip etsin.
- Sayfa sırası önerisi: Genel Bakış → Kömür-Rusya Bulgusu → Tedarikçi Riski & Ağ → Fiyat Bağlamı → Rezerv & Üretim → Ekonomik Etki (genelden özele, bulgudan bağlama doğru bir akış).
