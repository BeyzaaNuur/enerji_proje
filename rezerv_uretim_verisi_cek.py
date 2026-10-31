"""
Küresel kömür ve doğalgaz REZERV/ÜRETİM verisi — "tek kaynak riski"ni
gerçekten ölçmek için.

Şu ana kadarki veriler "kim ne kadar satıyor" gösteriyordu. Bu script ise
"dünyada bu kaynaktan ne kadar var, hangi ülke ne kadarına sahip" sorusuna
cevap veriyor — yani "Rusya kesilirse gerçekten alternatif var mı" sorusunu
test etmemizi sağlıyor.

Kaynak: Energy Institute "Statistical Review of World Energy" (ücretsiz,
yıllık yayınlanan, enerji sektörünün en çok referans gösterilen veri seti).

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install pandas openpyxl requests
Çalıştırma: python rezerv_uretim_verisi_cek.py

NOT: Bu, çok sayfalı (50+ sekme) büyük bir Excel dosyası (14 MB), indirmesi
biraz sürebilir. Script önce TÜM sayfa isimlerini ekrana basacak — hangi
sayfaların "Coal"/"Gas" + "reserves"/"production" içerdiğini görüp ona göre
ilerleyeceğiz. İlk çalıştırmada beklediğim tam sonucu bulamazsa script
bunun yerine bulduğu sayfa isimlerini ve örnek satırları basacak; o çıktıyı
bana gönder, kesin sayfa adlarına göre script'i bir sonraki adımda
kesinleştiririz.
"""
import re
import requests
import pandas as pd

DOSYA_URL = ("https://www.energyinst.org/__data/assets/excel_doc/0008/"
             "1656215/EI-Stats-Review-ALL-data.xlsx")
YEREL_DOSYA = "ei_statistical_review_ham.xlsx"

HEDEF_ULKELER = ["Russian Federation", "Russia", "Turkiye", "Turkey",
                  "Germany", "India", "Total World"]

# Aranacak sayfa adı anahtar kelimeleri: (içermesi gereken kelimeler)
ARANAN_SAYFALAR = [
    ["coal", "reserves"],
    ["coal", "production"],
    ["gas", "reserves"],
    ["gas", "production"],
]


def dosyayi_indir():
    print("Dosya indiriliyor (~14 MB, biraz sürebilir)...")
    # Bazı siteler tarayıcı olmayan istekleri (User-Agent'sız) 403 ile
    # reddediyor - tarayıcıymış gibi görünen bir başlık ekliyoruz
    basliklar = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
        "Referer": "https://www.energyinst.org/statistical-review/resources-and-data-downloads",
    }
    r = requests.get(DOSYA_URL, headers=basliklar, timeout=120)
    r.raise_for_status()
    with open(YEREL_DOSYA, "wb") as f:
        f.write(r.content)
    print(f"İndirildi: {YEREL_DOSYA} ({len(r.content)/1024/1024:.1f} MB)")


def sayfa_eslesir_mi(sayfa_adi: str, anahtar_kelimeler: list) -> bool:
    adi = sayfa_adi.lower()
    return all(k in adi for k in anahtar_kelimeler)


def ulke_satirlarini_bul(df: pd.DataFrame) -> pd.DataFrame:
    """İlk sütunda (genelde ülke isimleri) hedef ülkeleri arar."""
    ilk_sutun = df.columns[0]
    df[ilk_sutun] = df[ilk_sutun].astype(str)
    maske = df[ilk_sutun].apply(
        lambda hucre: any(u.lower() in hucre.lower() for u in HEDEF_ULKELER)
    )
    return df[maske]


def main():
    dosyayi_indir()

    xl = pd.ExcelFile(YEREL_DOSYA)
    print(f"\nToplam {len(xl.sheet_names)} sayfa bulundu.")

    eslesen_sayfalar = []
    for sayfa in xl.sheet_names:
        for anahtar_grup in ARANAN_SAYFALAR:
            if sayfa_eslesir_mi(sayfa, anahtar_grup):
                eslesen_sayfalar.append(sayfa)
                break

    if not eslesen_sayfalar:
        print("\nUYARI: Beklenen isimde sayfa bulunamadı. Tüm sayfa "
              "isimlerini aşağıda listeliyorum — bunları bana gönder:")
        for s in xl.sheet_names:
            print(" -", s)
        return

    print(f"\nEşleşen {len(eslesen_sayfalar)} sayfa bulundu: {eslesen_sayfalar}")

    tum_sonuclar = []
    for sayfa in eslesen_sayfalar:
        print(f"\n--- {sayfa} ---")
        # Başlık satırı genelde ilk birkaç satırdan sonra geliyor,
        # birkaç farklı header satırı deneyelim
        bulundu = False
        for header_satiri in [2, 3, 1, 0]:
            try:
                ham = pd.read_excel(YEREL_DOSYA, sheet_name=sayfa,
                                     header=header_satiri)
            except Exception:
                continue
            eslesenler = ulke_satirlarini_bul(ham)
            if not eslesenler.empty:
                print(f"  (header satırı {header_satiri} ile "
                      f"{len(eslesenler)} ülke satırı bulundu)")
                eslesenler = eslesenler.copy()
                eslesenler["kaynak_sayfa"] = sayfa
                tum_sonuclar.append(eslesenler)
                bulundu = True
                break
        if not bulundu:
            print("  UYARI: Bu sayfada hedef ülkeler bulunamadı, "
                  "ilk 5 satırı basıyorum (kontrol için):")
            print(pd.read_excel(YEREL_DOSYA, sheet_name=sayfa, header=None,
                                 nrows=5).to_string())

    if not tum_sonuclar:
        print("\nHiçbir sayfada hedef ülke satırı bulunamadı.")
        return

    cikti_dosyasi = "kuresel_rezerv_uretim_ham.csv"
    # Her sayfa farklı sütun yapısında olabileceği için şimdilik ham/geniş
    # formatta, sayfa bazlı ayrı ayrı kaydediyoruz
    with pd.ExcelWriter("kuresel_rezerv_uretim_ham.xlsx") as writer:
        for i, df in enumerate(tum_sonuclar):
            sayfa_adi = df["kaynak_sayfa"].iloc[0][:31]  # Excel sayfa adı sınırı
            df.to_excel(writer, sheet_name=sayfa_adi, index=False)

    print(f"\nBitti. Bulunan tüm ülke satırları şuraya kaydedildi: "
          f"kuresel_rezerv_uretim_ham.xlsx (her sekme bir kaynak sayfa)")
    print("Bu dosyayı bana gönder / ekran görüntüsü at, birlikte temiz "
          "tek tabloya çevirelim.")


if __name__ == "__main__":
    main()
