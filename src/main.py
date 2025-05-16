#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from srt_translator import SRTTranslator

def main():
    # Dossiers source et cible
    input_dir = "srt-files"
    output_dir = "srt-files-traduits"
    
    # Vérifie que le dossier source existe
    if not os.path.exists(input_dir):
        print(f"Erreur: Le dossier {input_dir} n'existe pas.")
        sys.exit(1)
    
    # Crée le dossier cible s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialise le traducteur avec llama3.2
    translator = SRTTranslator(model_name="llama3.2")
    
    # Liste tous les fichiers SRT dans le dossier source
    srt_files = [f for f in os.listdir(input_dir) if f.endswith('.srt')]
    
    if not srt_files:
        print(f"Aucun fichier SRT trouvé dans {input_dir}")
        sys.exit(1)
    
    print(f"Trouvé {len(srt_files)} fichiers SRT à traduire.")
    
    # Pour simplifier les tests, ne traiter que le premier fichier
    srt_file = srt_files[0]
    print(f"\nTraitement du fichier: {srt_file}")
    
    input_path = os.path.join(input_dir, srt_file)
    output_path = os.path.join(output_dir, f"fr_{srt_file}")
    
    # Options de traitement
    merge_duplicates = True  # Fusionner les sous-titres identiques
    filter_noise = True      # Filtrer les indications comme [music], [applause], etc.
    
    # Prétraitement du fichier SRT
    if filter_noise:
        print("Filtrage des sous-titres inutiles...")
        temp_file = os.path.join(output_dir, f"temp_{srt_file}")
        translator.filter_noise_subtitles(input_path, temp_file)
        input_path = temp_file
    
    if merge_duplicates:
        print("Fusion des sous-titres en doublon...")
        temp_file = os.path.join(output_dir, f"temp_{srt_file}")
        translator.merge_duplicate_subtitles(input_path, temp_file)
        input_path = temp_file
    
    # Pour un test rapide, limiter à 10 sous-titres maximum
    translator.translate_srt_file(input_path, output_path, batch_size=50, use_parallel=True)
    
    # Nettoyer les fichiers temporaires
    temp_file = os.path.join(output_dir, f"temp_{srt_file}")
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    print("\nTraduction terminée!")
    print(f"Le fichier traduit est disponible dans le dossier: {output_dir}")

if __name__ == "__main__":
    main() 