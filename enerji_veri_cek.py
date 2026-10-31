"""
Türkiye'nin enerji ithalatı — temiz veri çekme scripti.
Ham JSON'un karmaşık alanlarıyla (motCode, customsCode, netWgt vb.) hiç
uğraşmanıza gerek yok — bu script onları sizin için filtreliyor ve size
sadece 4 sütunlu, anlaşılır bir tablo bırakıyor.

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install comtradeapicall pandas
Çalıştırma: python enerji_veri_cek.py
"""
import comtradeapicall as ctc
import pandas as pd

# İncelediğimiz üç enerji kategorisi (HS kodu : okunabilir isim)
KATEGORILER = {
    "2701": "Kömür",
    "2709": "Ham Petrol",
    "2711": "Petrol Gazı (LNG + boru gazı)",
}

YIL = "2023"          # istediğiniz yılı değiştirebilirsiniz (örn. "2024")
TURKIYE_KODU = "792"  # UN Comtrade'de Türkiye'nin ülke kodu


def kategori_cek(hs_kodu: str, kategori_adi: str) -> pd.DataFrame:
    """Tek bir HS kodu için Türkiye'nin ülke bazlı ithalatını çeker,
    gereksiz sütunları atar, temiz bir tablo döndürür."""
    ham = ctc.previewFinalData(
        typeCode="C", freqCode="A", clCode="HS",
        period=YIL, reporterCode=TURKIYE_KODU, cmdCode=hs_kodu,
        flowCode="M",                     # M = İthalat (Import)
        partnerCode=None, partner2Code=None,
        customsCode=None, motCode="0",    # motCode=0 -> taşıma türüne bölünmesin
        includeDesc=True,                 # ülke isimlerini de getir
    )

    if ham is None or ham.empty:
        print(f"UYARI: {kategori_adi} için veri gelmedi, atlanıyor.")
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
    temiz["yil"] = YIL
    toplam = temiz["ithalat_tutari_usd"].sum()
    temiz["pay_yuzdesi"] = (temiz["ithalat_tutari_usd"] / toplam * 100).round(1)

    return temiz.sort_values("ithalat_tutari_usd", ascending=False)


def main():
    tum_kategoriler = []
    for hs_kodu, kategori_adi in KATEGORILER.items():
        print(f"Çekiliyor: {kategori_adi} ({YIL})...")
        df = kategori_cek(hs_kodu, kategori_adi)
        if not df.empty:
            tum_kategoriler.append(df)
            en_buyuk = df.iloc[0]
            print(f"  -> En büyük tedarikçi: {en_buyuk['tedarikci_ulke']} "
                  f"(%{en_buyuk['pay_yuzdesi']})")

    if not tum_kategoriler:
        print("Hiçbir kategori için veri çekilemedi.")
        return

    birlesik = pd.concat(tum_kategoriler, ignore_index=True)
    birlesik = birlesik[["kategori", "tedarikci_ulke", "ithalat_tutari_usd",
                          "pay_yuzdesi", "yil"]]

    cikti_dosyasi = "turkiye_enerji_ithalati_temiz.csv"
    birlesik.to_csv(cikti_dosyasi, index=False, encoding="utf-8-sig")
    print(f"\nBitti. Temiz veri şuraya kaydedildi: {cikti_dosyasi}")
    print(f"Toplam {len(birlesik)} satır, {len(KATEGORILER)} kategori.\n")
    print("İlk birkaç satır:")
    print(birlesik.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
