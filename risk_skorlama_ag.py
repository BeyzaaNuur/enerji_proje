"""
Tedarikçi-Ülke Ağı ve Tek-Kaynak Risk Skorlaması
==================================================

Girdi: turkiye_enerji_ithalati_coklu_yil.csv (kategori, tedarikci_ulke,
       ithalat_tutari_usd, pay_yuzdesi, yil)

Bu script iki şey yapar:

1) RİSK SKORLAMASI (kategori x yıl bazında)
   - HHI (Herfindahl-Hirschman Endeksi): Σ(pay_yuzdesi/100)²
     0 = tamamen dağılmış tedarik, 1 = tek kaynaktan %100 ithalat.
     ABD Rekabet Kurumu (DOJ/FTC) HHI > 0.25'i "yüksek yoğunlaşma" sayar,
     biz de bu eşiği referans alıyoruz.
   - Efektif tedarikçi sayısı = 1/HHI (yorumlanması kolay bir türev metrik)
   - risk_skoru_0_100 = HHI * 100 (basit, şeffaf, "kara kutu" olmayan bir skor)
   - delta_hhi_2015_2023: yoğunlaşmanın zaman içinde artıp artmadığı
     (skora dahil edilmiyor, ayrı bir "trend" sütunu olarak veriliyor —
     amaç: tek bir sayının arkasına gerçek örüntüyü gizlememek)

2) AĞ (NETWORK) ANALİZİ (2023 verisiyle, bipartite graf)
   - Düğümler: enerji kategorileri + tedarikçi ülkeler
   - Kenarlar: ithalat tutarı (USD)
   - Ülke bazında "kaç kategoriye tedarikçi" (derece) hesaplanıyor —
     birden fazla kategoride görünen ülke (örn. Rusya), tek bir kategoride
     değil, sistemin genelinde kritik hale gelir ("sistemik tedarikçi").

KENDİ BİLGİSAYARINIZDA çalıştırın (bulut sandbox'ında değil).
Kurulum: pip install pandas networkx matplotlib
Çalıştırma: python risk_skorlama_ag.py

Çıktılar:
  - risk_skorlari_kategori_yil.csv
  - tedarikci_merkezilik_2023.csv
  - enerji_tedarik_agi_2023.png
"""
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GIRDI_DOSYASI = "turkiye_enerji_ithalati_coklu_yil.csv"
SON_YIL = 2023
HHI_YUKSEK_ESIK = 0.25  # DOJ/FTC "yüksek yoğunlaşma" eşiği


def veriyi_yukle():
    df = pd.read_csv(GIRDI_DOSYASI, sep=";", decimal=",", encoding="utf-8-sig")
    df["ithalat_tutari_usd"] = pd.to_numeric(df["ithalat_tutari_usd"], errors="coerce")
    df["pay_yuzdesi"] = pd.to_numeric(df["pay_yuzdesi"], errors="coerce")
    return df


def risk_skorlarini_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    """Her (kategori, yıl) çifti için HHI tabanlı risk skoru."""
    sonuclar = []
    for (kategori, yil), grup in df.groupby(["kategori", "yil"]):
        # pay_yuzdesi zaten CSV'de var ama güvenlik için burada da yeniden hesaplıyoruz
        toplam = grup["ithalat_tutari_usd"].sum()
        paylar = grup["ithalat_tutari_usd"] / toplam  # 0-1 arası oran

        hhi = (paylar ** 2).sum()
        efektif_tedarikci = 1 / hhi if hhi > 0 else float("nan")
        tedarikci_sayisi = grup["tedarikci_ulke"].nunique()

        en_buyuk = grup.sort_values("ithalat_tutari_usd", ascending=False).iloc[0]

        sonuclar.append({
            "kategori": kategori,
            "yil": yil,
            "tedarikci_sayisi": tedarikci_sayisi,
            "top1_ulke": en_buyuk["tedarikci_ulke"],
            "top1_payi_yuzde": round(en_buyuk["ithalat_tutari_usd"] / toplam * 100, 1),
            "hhi": round(hhi, 4),
            "efektif_tedarikci_sayisi": round(efektif_tedarikci, 2),
            "risk_skoru_0_100": round(hhi * 100, 1),
            "yuksek_yogunlasma_mi": hhi > HHI_YUKSEK_ESIK,
        })

    sonuc_df = pd.DataFrame(sonuclar).sort_values(["kategori", "yil"])

    # Trend: 2015 -> son yıl HHI değişimi (kategori bazında)
    trend = sonuc_df.pivot(index="kategori", columns="yil", values="hhi")
    ilk_yil = trend.columns.min()
    son_yil_kolonu = trend.columns.max()
    trend_delta = (trend[son_yil_kolonu] - trend[ilk_yil]).rename("delta_hhi_ilk_son_yil")
    sonuc_df = sonuc_df.merge(trend_delta, on="kategori", how="left")

    return sonuc_df


def tedarikci_merkeziligi_hesapla(df: pd.DataFrame, yil: int) -> tuple[pd.DataFrame, nx.Graph]:
    """Belirli bir yıl için bipartite (kategori-ülke) ağ kurar,
    ülke bazında 'kaç kategoriye tedarikçi' ve toplam hacmi hesaplar."""
    yil_df = df[df["yil"] == yil]

    G = nx.Graph()
    for kategori in yil_df["kategori"].unique():
        G.add_node(kategori, tip="kategori")

    for _, satir in yil_df.iterrows():
        ulke = satir["tedarikci_ulke"]
        kategori = satir["kategori"]
        tutar = satir["ithalat_tutari_usd"]
        if not G.has_node(ulke):
            G.add_node(ulke, tip="ulke")
        if G.has_edge(ulke, kategori):
            G[ulke][kategori]["weight"] += tutar
        else:
            G.add_edge(ulke, kategori, weight=tutar)

    ulke_nodlari = [n for n, d in G.nodes(data=True) if d.get("tip") == "ulke"]
    merkezilik = []
    for ulke in ulke_nodlari:
        komsu_kategoriler = list(G.neighbors(ulke))
        toplam_hacim = sum(G[ulke][k]["weight"] for k in komsu_kategoriler)
        merkezilik.append({
            "ulke": ulke,
            "kac_kategoriye_tedarikci": len(komsu_kategoriler),
            "kategoriler": ", ".join(sorted(komsu_kategoriler)),
            "toplam_hacim_usd": round(toplam_hacim, 0),
            "sistemik_tedarikci_mi": len(komsu_kategoriler) >= 2,
        })

    merkezilik_df = pd.DataFrame(merkezilik).sort_values(
        ["kac_kategoriye_tedarikci", "toplam_hacim_usd"], ascending=[False, False]
    )
    return merkezilik_df, G


def agi_gorsellestir(G: nx.Graph, yil: int, dosya_adi: str, top_n_ulke: int = 15):
    """Ağı görselleştirir. Okunabilirlik için sadece en büyük top_n_ulke
    hacimli ülkeyi + tüm kategori düğümlerini gösterir."""
    kategori_nodlari = [n for n, d in G.nodes(data=True) if d.get("tip") == "kategori"]
    ulke_nodlari = [n for n, d in G.nodes(data=True) if d.get("tip") == "ulke"]

    ulke_hacimleri = {
        u: sum(G[u][k]["weight"] for k in G.neighbors(u)) for u in ulke_nodlari
    }
    en_buyuk_ulkeler = sorted(ulke_hacimleri, key=ulke_hacimleri.get, reverse=True)[:top_n_ulke]

    alt_graf = G.subgraph(kategori_nodlari + en_buyuk_ulkeler)

    pos = nx.bipartite_layout(alt_graf, kategori_nodlari) if nx.is_bipartite(alt_graf) \
        else nx.spring_layout(alt_graf, seed=42, k=0.8)

    import textwrap
    fig, ax = plt.subplots(figsize=(14, 9))

    # Kategori düğümlerini biraz sola kaydır, ülke etiketlerine yer aç
    for n in kategori_nodlari:
        pos[n] = (pos[n][0] - 0.15, pos[n][1])

    kenar_agirliklari = [alt_graf[u][v]["weight"] for u, v in alt_graf.edges()]
    max_agirlik = max(kenar_agirliklari) if kenar_agirliklari else 1
    kenar_genislikleri = [1 + 6 * (w / max_agirlik) for w in kenar_agirliklari]

    nx.draw_networkx_edges(alt_graf, pos, width=kenar_genislikleri, alpha=0.35,
                            edge_color="#5A5A5A", ax=ax)

    nx.draw_networkx_nodes(alt_graf, pos, nodelist=kategori_nodlari,
                            node_color="#1F3B57", node_shape="s",
                            node_size=4200, ax=ax)
    nx.draw_networkx_nodes(alt_graf, pos, nodelist=en_buyuk_ulkeler,
                            node_color="#C0392B", node_shape="o",
                            node_size=[300 + 900 * (ulke_hacimleri[u] / max(ulke_hacimleri.values())) for u in en_buyuk_ulkeler],
                            alpha=0.85, ax=ax)

    kategori_etiketleri = {n: "\n".join(textwrap.wrap(n, 14)) for n in kategori_nodlari}
    nx.draw_networkx_labels(alt_graf, pos, font_size=9, font_color="white",
                             labels=kategori_etiketleri, ax=ax)

    ulke_pos = {u: (pos[u][0] + 0.05, pos[u][1]) for u in en_buyuk_ulkeler}
    for u in en_buyuk_ulkeler:
        ax.annotate(u, xy=pos[u], xytext=ulke_pos[u], fontsize=8, va="center")

    ax.set_title(f"Türkiye Enerji İthalatı Tedarikçi Ağı ({yil}) — en büyük {top_n_ulke} tedarikçi ülke",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(-1.35, 1.55)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(dosya_adi, dpi=150)
    plt.close()


def main():
    df = veriyi_yukle()

    print("=== Risk Skorlaması (kategori x yıl) ===")
    risk_df = risk_skorlarini_hesapla(df)
    risk_df.to_csv("risk_skorlari_kategori_yil.csv", index=False,
                    encoding="utf-8-sig", sep=";", decimal=",")
    print(risk_df[risk_df["yil"] == SON_YIL].to_string(index=False))

    print(f"\n=== Tedarikçi Merkeziliği ({SON_YIL}) ===")
    merkezilik_df, G = tedarikci_merkeziligi_hesapla(df, SON_YIL)
    merkezilik_df.to_csv("tedarikci_merkezilik_2023.csv", index=False,
                          encoding="utf-8-sig", sep=";", decimal=",")
    print(merkezilik_df[merkezilik_df["sistemik_tedarikci_mi"]].to_string(index=False))

    print(f"\n=== Ağ Görseli Oluşturuluyor ({SON_YIL}) ===")
    agi_gorsellestir(G, SON_YIL, "enerji_tedarik_agi_2023.png")
    print("Kaydedildi: enerji_tedarik_agi_2023.png")

    print("\nBitti. 3 dosya oluşturuldu:")
    print(" - risk_skorlari_kategori_yil.csv")
    print(" - tedarikci_merkezilik_2023.csv")
    print(" - enerji_tedarik_agi_2023.png")


if __name__ == "__main__":
    main()
