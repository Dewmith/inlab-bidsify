import os
from pathlib import Path
from datetime import datetime

# Dossier racine
base_dir = Path("/Volumes/x9/INITIAL_DATABASE")

# Fonction pour renommer les fichiers dans un sous-dossier
def traiter_sous_dossier(dossier):
    fichiers = list(dossier.glob("*.bdf"))
    if not fichiers:
        return

    # Collecte des dates de création
    fichiers_dates = []
    for fichier in fichiers:
        stat = fichier.stat()
        try:
            created_time = stat.st_birthtime
        except AttributeError:
            created_time = stat.st_ctime
        created_date = datetime.fromtimestamp(created_time).date()
        fichiers_dates.append((fichier, created_date))

    # Identifier 2 dates distinctes dans le sous-dossier
    unique_dates = sorted(set(date for _, date in fichiers_dates))
    if len(unique_dates) != 2:
        print(f"[{dossier}] - Ignoré : {len(unique_dates)} date(s) trouvée(s)")
        return

    jour_label = {
        unique_dates[0]: "day1",
        unique_dates[1]: "day2"
    }

    # Renommage
    for fichier, date in fichiers_dates:
        label = jour_label[date]
        parent = fichier.parent
        stem = fichier.stem
        suffix = fichier.suffix
        if label in stem:
            continue
        nouveau_nom = f"{stem}_{label}{suffix}"
        nouveau_chemin = parent / nouveau_nom
        fichier.rename(nouveau_chemin)
        print(f"Renommé dans {dossier}: {fichier.name} → {nouveau_nom}")

# Traitement récursif de tous les sous-répertoires
for sous_dossier in base_dir.rglob("*"):
    if sous_dossier.is_dir():
        traiter_sous_dossier(sous_dossier)
