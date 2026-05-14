import os
folder = r'C:\Users\rayen\Desktop\SMA assistant\data\uploads'
keep = {'01_donnees_vente.csv','02_analyse_region.csv','03_analyse_categorie.csv','04_analyse_canaux.csv','05_kpis_globaux.csv'}
for f in os.listdir(folder):
    if f not in keep:
        os.remove(os.path.join(folder, f))
        print('Supprime:', f)
print('Restants:', os.listdir(folder))
