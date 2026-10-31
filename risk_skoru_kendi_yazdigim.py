import pandas as pd
import networkx as nx 
import matplotlib.pyplot as plt

GİRDİ_DOSYASİ = "turkiye_enerji_ithalati_coklu_yil.csv"
df =  pd.read_csv (GİRDİ_DOSYASİ, sep=";", decimal = ",", encoding="utf-8-sig")
print(df.head())

sonuclar = []
for (kategori , yil ) , grup in df.groupby(["kategori","yil"]):
        toplam = grup["ithalat_tutari_usd"].sum()
        paylar = grup["ithalat_tutari_usd"] / toplam
        hhi = (paylar ** 2).sum()

        sonuclar.append({
                "kategori": kategori,
                "yil":yil,
                "hhi":hhi,
                "risk_skoru": hhi*100
        })

        risk_df = pd.DataFrame(sonuclar)
print(risk_df)       

risk_df.to_csv("risk_skorlari_ogrenme.csv", index=False,
                encoding="utf-8-sig", sep=";", decimal=",")
print("Kaydedildi: risk_skorlari_ogrenme.csv")

veri_2023 =  df[df["yil"] == 2023]
G = nx.Graph()

for kategori in veri_2023["kategori"].unique():
    G.add_node(kategori)

for indeks, satir in veri_2023.iterrows():
    ulke = satir["tedarikci_ulke"]
    kategori = satir["kategori"]
    tutar = satir["ithalat_tutari_usd"]
    G.add_edge(ulke, kategori, weight=tutar)

print("Toplam düğüm sayısı:", G.number_of_nodes())
print("Toplam bağlantı sayısı:", G.number_of_edges())

komsular = list(G.neighbors("Kömür"))
print("Kömür'ün tedarikçileri:", komsular)

rusya_komsulari = list(G.neighbors("Russian Federation"))
print("Rusya hangi kategorilere tedarikçi:", rusya_komsulari)

print("Toplam düğüm sayısı:", G.number_of_nodes())
print("Toplam bağlantı sayısı:", G.number_of_edges())

komsular = list(G.neighbors("Kömür"))
print("Kömür'ün tedarikçileri:", komsular)



ulke_hacimleri = {}

for ulke in veri_2023["tedarikci_ulke"].unique():
    komsu_kategoriler = list(G.neighbors(ulke))
    toplam_hacim = 0
    for kat in komsu_kategoriler:
        toplam_hacim = toplam_hacim + G[ulke][kat]["weight"]
    ulke_hacimleri[ulke] = toplam_hacim

    en_buyukler = sorted(ulke_hacimleri, key=ulke_hacimleri.get, reverse=True)
en_buyuk_15 = en_buyukler[:15]
print("En büyük 15 tedarikçi:", en_buyuk_15)

gosterilecek_dugumler = list(veri_2023["kategori"].unique()) + en_buyuk_15
alt_graf = G.subgraph(gosterilecek_dugumler)

pos = nx.bipartite_layout(alt_graf, list(veri_2023["kategori"].unique()))

nx.draw(alt_graf, pos, with_labels=True, node_size=800, font_size=8)
plt.savefig("agimiz_temiz.png", dpi=150)
print("Kaydedildi: agimiz_temiz.png")