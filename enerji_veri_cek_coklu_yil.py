"""
Türkiye'nin enerji ithalatı — ÇOKLU YIL, temiz veri çekme scripti.
Tek fark: enerji_veri_cek.py sadece 1 yıl çekiyordu, bu script birden
fazla yılı art arda çekip TEK bir tabloda birleştiriyor. Böylece "Rusya'nın
%61,9'luk payı hep mi böyleydi, yoksa yeni mi oluştu" gibi trend sorularına
cevap verebilirsin.

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install comtradeapicall pandas   (zaten kurulu olmalı)
Çalıştırma: python enerji_veri_cek_coklu_yil.py

NOT: Her yıl x her kategori için ayrı bir API isteği atılıyor (9 yıl x 3
kategori = 27 istek). UN Comtrade'in ücretsiz "preview" API'si dakikada
belli bir istek sınırı koyuyor, o yüzden aralara küçük bir bekleme (sleep)
koydum — script biraz yavaş çalışacak (birkaç dakika sürebilir), bu normal,
sabırlı ol.
"""
import time
import comtradeapicall as ctc
import pandas as pd

# İncelediğimiz üç enerji kategorisi (HS kodu : okunabilir isim)
KATEGORILER = {
    "2701": "Kömür",
    "2710": "Rafine Petrol Ürünleri",  # 2709 (Ham Petrol) çıkarıldı: Türkiye bu
                                        # kalemde ülke bazlı veri raporlamıyor
                                        # (UN Comtrade'de doğrulandı, 2015-2023
                                        # arası tüm yıllarda 0 satır dönüyor)
    "2711": "Petrol Gazı (LNG + boru gazı)",
}

# Çekilecek yıllar — istersen aralığı genişlet/daralt (Comtrade genelde
# 1990'lara kadar veri tutuyor ama eski yıllarda bazı ülkeler eksik olabilir)
YILLAR = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]

TURKIYE_KODU = "792"  # UN Comtrade'de Türkiye'nin ülke kodu
BEKLEME_SANIYE = 2    # istekler arası bekleme (API'yi yormamak için)


def kategori_yil_cek(hs_kodu: str, kategori_adi: str, yil: int) -> pd.DataFrame:
    """Tek bir HS kodu + tek bir yıl için Türkiye'nin ülke bazlı ithalatını
    çeker, gereksiz sütunları atar, temiz bir tablo döndürür."""
    ham = ctc.previewFinalData(
        typeCode="C", freqCode="A", clCode="HS",
        period=str(yil), reporterCode=TURKIYE_KODU, cmdCode=hs_kodu,
        flowCode="M",                     # M = İthalat (Import)
        partnerCode=None, partner2Code=None,
        customsCode=None, motCode="0",    # motCode=0 -> taşıma türüne bölünmesin
        includeDesc=True,                 # ülke isimlerini de getir
    )

    if ham is None or ham.empty:
        print(f"  UYARI: {kategori_adi} / {yil} için veri gelmedi, atlanıyor.")
        return pd.DataFrame()

    # "World" (dünya toplamı) satırını at, sadece ülke satırlarını bırak
    ulke_bazli = ham[ham["partnerCode"] != 0].copy()

    # Sadece işimize yarayan sütunları seç, Türkçe isimlendir
    temiz = ulke_bazli[["partnerDesc", "cifvalue"]].rename(
        columns={"partnerDesc": "tedarikci_ulke", "cifvalue": "ithalat_tutari_usd"}
    )

    # Aynı ülke birden fazla satırda geçebilir (farklı gümrük rejimleri vb.) - topla
    temiz = temiz.groupby("tedarikci_ulke", as_index=False)["ithalat_tutari_usd"].sum()

    temiz["kategori"] = kategori_adi
    temiz["yil"] = yil
    toplam = temiz["ithalat_tutari_usd"].sum()
    temiz["pay_yuzdesi"] = (temiz["ithalat_tutari_usd"] / toplam * 100).round(1)

    return temiz.sort_values("ithalat_tutari_usd", ascending=False)


def main():
    tum_sonuclar = []
    toplam_istek = len(KATEGORILER) * len(YILLAR)
    sayac = 0

    for hs_kodu, kategori_adi in KATEGORILER.items():
        for yil in YILLAR:
            sayac += 1
            print(f"[{sayac}/{toplam_istek}] Çekiliyor: {kategori_adi} ({yil})...")
            df = kategori_yil_cek(hs_kodu, kategori_adi, yil)
            if not df.empty:
                tum_sonuclar.append(df)
                en_buyuk = df.iloc[0]
                print(f"  -> En büyük tedarikçi: {en_buyuk['tedarikci_ulke']} "
                      f"(%{en_buyuk['pay_yuzdesi']})")
            time.sleep(BEKLEME_SANIYE)

    if not tum_sonuclar:
        print("Hiçbir kategori/yıl için veri çekilemedi.")
        return

    birlesik = pd.concat(tum_sonuclar, ignore_index=True)
    birlesik = birlesik[["kategori", "tedarikci_ulke", "ithalat_tutari_usd",
                          "pay_yuzdesi", "yil"]]
    birlesik = birlesik.sort_values(["kategori", "yil", "ithalat_tutari_usd"],
                                     ascending=[True, True, False])

    cikti_dosyasi = "turkiye_enerji_ithalati_coklu_yil.csv"
    # sep=";" ve decimal="," -> Türkçe Windows/Excel/Power Query bu formatı
    # otomatik doğru okur (nokta ondalık ayırıcı olsaydı sayılar karışırdı)
    birlesik.to_csv(cikti_dosyasi, index=False, encoding="utf-8-sig",
                     sep=";", decimal=",")
    print(f"\nBitti. Temiz veri şuraya kaydedildi: {cikti_dosyasi}")
    print(f"Toplam {len(birlesik)} satır, {len(KATEGORILER)} kategori, "
          f"{len(YILLAR)} yıl.\n")

    # Kömür - Rusya'nın yıl bazında payını hızlıca ekrana bas (kontrol için)
    kontrol = birlesik[(birlesik["kategori"] == "Kömür") &
                        (birlesik["tedarikci_ulke"] == "Russian Federation")]
    if not kontrol.empty:
        print("Kömürde Rusya'nın payı, yıllara göre:")
        print(kontrol[["yil", "pay_yuzdesi"]].to_string(index=False))


if __name__ == "__main__":
    main()
