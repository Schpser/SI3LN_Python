# script_remove_bg.py
from rembg import remove
import os

# Dossier contenant les images
input_folder = r"D:\gamesss\SI3LN_Python-master\assets\players\player_8"
# Dossier de sortie pour les images avec fond transparent
output_folder = os.path.join(input_folder, "output")
os.makedirs(output_folder, exist_ok=True)

# Parcours des fichiers dans le dossier
for filename in os.listdir(input_folder):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        with open(input_path, "rb") as i:
            input_data = i.read()
            output_data = remove(input_data)
        with open(output_path, "wb") as o:
            o.write(output_data)
        print(f"Traitée : {filename}")

print("✅ Toutes les images ont été traitées et sauvegardées dans le dossier 'output'.")
