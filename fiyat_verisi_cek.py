"""
Küresel kömür ve doğalgaz fiyatları — Dünya Bankası "Pink Sheet" verisinden
temiz bir tablo çıkarıyor.

Amaç: "AB ambargosu sonrası Rus kömürü/gazı ucuzladı mı" hipotezini test
etmek. Bu script Dünya Bankası'nın aylık emtia fiyat dosyasını indirip,
kömür ve doğalgaz fiyat sütunlarını bulup, yıllık ortalamaya çeviriyor.

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install pandas openpyxl requests
Çalıştırma: python fiyat_verisi_cek.py

NOT: Dünya Bankası'nın dosya yapısı zamanla küçük değişiklikler
gösterebiliyor, o yüzden script önce hangi sütunları bulduğunu ekrana
basıyor — "beklenmedik" bir şey görürsen bana o çıktıyı gönder, birlikte
düzeltiriz.
"""
import re
import requests
import pandas as pd

# Dünya Bankası "Pink Sheet" aylık emtia fiyat dosyası (güncel link)
DOSYA_URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
YEREL_DOSYA = "pink_sheet_ham.xlsx"


def dosyayi_indir():
    print("Dosya indiriliyor (birkaç MB, biraz sürebilir)...")
    r = requests.get(DOSYA_URL, timeout=60)
    r.raise_for_status()
    with open(YEREL_DOSYA, "wb") as f:
        f.write(r.content)
    print(f"İndirildi: {YEREL_DOSYA} ({len(r.content)/1024:.0f} KB)")


def kolon_bul(kolonlar, anahtar_kelimeler):
    """Sütun isimleri arasında anahtar kelimeleri içerenleri bulur."""
    bulunanlar = []
    for kolon in kolonlar:
        kolon_str = str(kolon).lower()
        if any(k.lower() in kolon_str for k in anahtar_kelimeler):
            bulunanlar.append(kolon)
    return bulunanlar


def main():
    dosyayi_indir()

    # "Monthly Prices" sayfasını oku — 4. satır başlık (0-indeksli: 4)
    ham = pd.read_excel(YEREL_DOSYA, sheet_name="Monthly Prices", header=4)
    print(f"\nToplam {len(ham.columns)} sütun bulundu. İlk sütun (tarih): "
          f"{ham.columns[0]!r}")

    kömür_kolonlari = kolon_bul(ham.columns, ["coal"])
    gaz_kolonlari = kolon_bul(ham.columns, ["natural gas", "lng"])

    print(f"\nKömürle ilgili bulunan sütunlar: {kömür_kolonlari}")
    print(f"Doğalgazla ilgili bulunan sütunlar: {gaz_kolonlari}")

    if not kömür_kolonlari and not gaz_kolonlari:
        print("\nUYARI: Beklenen sütunlar bulunamadı. Aşağıdaki tüm sütun "
              "listesini bana gönder, birlikte düzeltelim:")
        print(list(ham.columns))
        return

    tarih_kolonu = ham.columns[0]
    secili_kolonlar = [tarih_kolonu] + kömür_kolonlari + gaz_kolonlari
    veri = ham[secili_kolonlar].copy()
    veri = veri.rename(columns={tarih_kolonu: "ay"})

    # "ay" sütunu genelde "1990M01" gibi bir metin - yıl ayıklayalım
    veri["yil"] = veri["ay"].astype(str).str.extract(r"(\d{4})")
    veri = veri.dropna(subset=["yil"])
    veri["yil"] = veri["yil"].astype(int)
    veri = veri[(veri["yil"] >= 2015) & (veri["yil"] <= 2023)]

    # Yıllık ortalamaya indirge (aylık veriyi 2015-2023 için özetle)
    sayisal_kolonlar = kömür_kolonlari + gaz_kolonlari
    for k in sayisal_kolonlar:
        veri[k] = pd.to_numeric(veri[k], errors="coerce")

    yillik = veri.groupby("yil", as_index=False)[sayisal_kolonlar].mean().round(2)

    cikti_dosyasi = "kuresel_enerji_fiyatlari_yillik.csv"
    yillik.to_csv(cikti_dosyasi, index=False, encoding="utf-8-sig",
                   sep=";", decimal=",")
    print(f"\nBitti. Yıllık ortalama fiyatlar şuraya kaydedildi: {cikti_dosyasi}")
    print(yillik.to_string(index=False))


if __name__ == "__main__":
    main()
