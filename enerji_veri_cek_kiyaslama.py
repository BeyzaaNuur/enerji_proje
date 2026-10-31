"""
Kıyaslama ülkeleri — Rusya kömürüne yönelişin sadece Türkiye'ye özgü mü,
yoksa daha geniş bir eğilimin parçası mı olduğunu görmek için.

Aynı Kömür (HS 2701) sorgusunu üç ülke için çalıştırıyor:
  - Türkiye  (elindeki veriyle karşılaştırma/doğrulama için de kullanılabilir)
  - Almanya  (AB üyesi, ambargoya tam uyması beklenen "kontrol grubu")
  - Hindistan (Türkiye gibi, savaş sonrası Rus kömürüne/petrolüne belirgin
               şekilde yöneldiği bilinen bir ülke)

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install comtradeapicall pandas   (zaten kurulu olmalı)
Çalıştırma: python enerji_veri_cek_kiyaslama.py

NOT: 3 ülke x 9 yıl = 27 istek atılacak, aralara 2 saniye bekleme koydum,
script birkaç dakika sürebilir.
"""
import time
import comtradeapicall as ctc
import pandas as pd

RAPORTOR_ULKELER = {
    "792": "Türkiye",
    "276": "Almanya",
    "699": "Hindistan",
}

HS_KODU = "2701"       # Kömür
KATEGORI_ADI = "Kömür"
YILLAR = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
BEKLEME_SANIYE = 2


def ulke_yil_cek(raportor_kodu: str, raportor_adi: str, yil: int) -> pd.DataFrame:
    """Tek bir raportör ülke + tek bir yıl için Kömür ithalatının ülke bazlı
    kırılımını çeker, temiz bir tablo döndürür."""
    ham = ctc.previewFinalData(
        typeCode="C", freqCode="A", clCode="HS",
        period=str(yil), reporterCode=raportor_kodu, cmdCode=HS_KODU,
        flowCode="M",
        partnerCode=None, partner2Code=None,
        customsCode=None, motCode="0",
        includeDesc=True,
    )

    if ham is None or ham.empty:
        print(f"  UYARI: {raportor_adi} / {yil} için veri gelmedi, atlanıyor.")
        return pd.DataFrame()

    ulke_bazli = ham[ham["partnerCode"] != 0].copy()
    temiz = ulke_bazli[["partnerDesc", "cifvalue"]].rename(
        columns={"partnerDesc": "tedarikci_ulke", "cifvalue": "ithalat_tutari_usd"}
    )
    temiz = temiz.groupby("tedarikci_ulke", as_index=False)["ithalat_tutari_usd"].sum()

    temiz["raportor_ulke"] = raportor_adi
    temiz["kategori"] = KATEGORI_ADI
    temiz["yil"] = yil
    toplam = temiz["ithalat_tutari_usd"].sum()
    temiz["pay_yuzdesi"] = (temiz["ithalat_tutari_usd"] / toplam * 100).round(1)

    return temiz.sort_values("ithalat_tutari_usd", ascending=False)


def main():
    tum_sonuclar = []
    toplam_istek = len(RAPORTOR_ULKELER) * len(YILLAR)
    sayac = 0

    for raportor_kodu, raportor_adi in RAPORTOR_ULKELER.items():
        for yil in YILLAR:
            sayac += 1
            print(f"[{sayac}/{toplam_istek}] Çekiliyor: {raportor_adi} ({yil})...")
            df = ulke_yil_cek(raportor_kodu, raportor_adi, yil)
            if not df.empty:
                tum_sonuclar.append(df)
                rusya = df[df["tedarikci_ulke"] == "Russian Federation"]
                pay = rusya.iloc[0]["pay_yuzdesi"] if not rusya.empty else 0
                print(f"  -> Rusya payı: %{pay}")
            time.sleep(BEKLEME_SANIYE)

    if not tum_sonuclar:
        print("Hiçbir ülke/yıl için veri çekilemedi.")
        return

    birlesik = pd.concat(tum_sonuclar, ignore_index=True)
    birlesik = birlesik[["raportor_ulke", "kategori", "tedarikci_ulke",
                          "ithalat_tutari_usd", "pay_yuzdesi", "yil"]]
    birlesik = birlesik.sort_values(["raportor_ulke", "yil", "ithalat_tutari_usd"],
                                     ascending=[True, True, False])

    cikti_dosyasi = "kiyaslama_ulkeleri_komur.csv"
    birlesik.to_csv(cikti_dosyasi, index=False, encoding="utf-8-sig",
                     sep=";", decimal=",")
    print(f"\nBitti. Kaydedildi: {cikti_dosyasi}")

    # Rusya payının 3 ülkede yıl bazında nasıl değiştiğini hızlıca göster
    kontrol = birlesik[birlesik["tedarikci_ulke"] == "Russian Federation"]
    if not kontrol.empty:
        ozet = kontrol.pivot(index="yil", columns="raportor_ulke", values="pay_yuzdesi")
        print("\nRusya'nın kömür ithalatındaki payı, ülkelere göre:")
        print(ozet.to_string())


if __name__ == "__main__":
    main()
