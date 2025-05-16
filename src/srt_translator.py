#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pysrt
import re
from tqdm import tqdm
from ollama_translator import OllamaTranslator

class SRTTranslator:
    """Traducteur de fichiers SRT de l'anglais vers le français utilisant Ollama"""
    
    def __init__(self, model_name="mistral"):
        """Initialisation avec le modèle spécifique"""
        print(f"Initialisation du traducteur avec le modèle {model_name}...")
        self.translator = OllamaTranslator(model_name=model_name)
    
    def translate_text(self, text):
        """Traduire un texte de l'anglais vers le français"""
        if not text or text.strip() == "":
            return ""
        return self.translator.translate(text)
    
    def translate_batch(self, texts, batch_size=10):
        """Traduire une liste de textes par lots"""
        print(f"Traduction de {len(texts)} sous-titres...")
        return self.translator.translate_batch(texts, batch_size)
    
    def filter_noise_subtitles(self, input_file, output_file=None):
        """Filtrer les sous-titres de bruit comme [musique], [applaudissements], etc."""
        print(f"Chargement du fichier {input_file}...")
        try:
            subs = pysrt.open(input_file, encoding='utf-8')
            
            filtered_subs = pysrt.SubRipFile()
            
            # Modèle pour détecter les sous-titres de bruit
            noise_pattern = re.compile(r'^\s*\[(music|applause|silence|sound|musique|bruit|applaudissements|silence)\]\s*$', re.IGNORECASE)
            
            for sub in subs:
                text = sub.text.strip()
                
                # Ignorer les sous-titres de bruit
                if noise_pattern.match(text) or not text:
                    continue
                
                # Nettoyer les crochets dans les sous-titres normaux
                cleaned_text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text).strip()
                if cleaned_text:
                    new_sub = pysrt.SubRipItem()
                    new_sub.index = len(filtered_subs) + 1
                    new_sub.start = sub.start
                    new_sub.end = sub.end
                    new_sub.text = cleaned_text
                    filtered_subs.append(new_sub)
            
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                filtered_subs.save(output_file, encoding='utf-8')
                print(f"Sous-titres filtrés sauvegardés dans: {output_file}")
            
            return filtered_subs
        except Exception as e:
            print(f"Erreur lors du filtrage des sous-titres: {str(e)}")
            if output_file and os.path.exists(input_file):
                # En cas d'échec, simplement copier le fichier d'entrée
                import shutil
                shutil.copy(input_file, output_file)
                print(f"Fichier d'origine copié à {output_file}")
                return pysrt.open(input_file, encoding='utf-8')
            raise
    
    def merge_duplicate_subtitles(self, input_file, output_file=None):
        """Fusionner les sous-titres dupliqués ou fragmentés"""
        print(f"Chargement du fichier {input_file}...")
        try:
            subs = pysrt.open(input_file, encoding='utf-8')
            
            merged_subs = pysrt.SubRipFile()
            
            i = 0
            while i < len(subs):
                current_sub = subs[i]
                current_text = current_sub.text.strip()
                
                if not current_text:
                    i += 1
                    continue
                
                # Recherche de fragments consécutifs à regrouper
                j = i + 1
                grouped_texts = [current_text]
                max_chars = 80  # Nombre maximal de caractères par sous-titre pour la lisibilité
                
                # Tenter de fusionner avec les sous-titres suivants si approprié
                while j < len(subs) and len('\n'.join(grouped_texts)) < max_chars:
                    next_text = subs[j].text.strip()
                    
                    # Vérifier si ce sous-titre devrait être fusionné
                    time_gap = (subs[j].start.ordinal - current_sub.end.ordinal) / 1000 < 1000  # écart < 1s
                    
                    # Vérifier si les sous-titres sont liés
                    is_duplicate = next_text == current_text
                    
                    # Vérifier s'il s'agit d'un fragment de phrase
                    ends_with_punct = current_text and current_text[-1] in '.!?'
                    starts_with_lowercase = next_text and len(next_text) > 0 and next_text[0].islower()
                    
                    # Décider si on fusionne
                    should_merge = (
                        is_duplicate or 
                        time_gap or 
                        (not ends_with_punct and starts_with_lowercase)
                    )
                    
                    if should_merge:
                        # Étendre la durée du sous-titre actuel
                        current_sub.end = subs[j].end
                        
                        # Ajouter aux fragments si pas dupliqué et pas vide
                        if next_text and next_text not in grouped_texts:
                            grouped_texts.append(next_text)
                        
                        j += 1
                    else:
                        break
                
                # Créer le texte joint
                joined_text = self._join_subtitles(grouped_texts)
                
                # Ajouter le sous-titre fusionné
                new_sub = pysrt.SubRipItem()
                new_sub.index = len(merged_subs) + 1
                new_sub.start = current_sub.start
                new_sub.end = current_sub.end
                new_sub.text = joined_text
                merged_subs.append(new_sub)
                
                i = j
            
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                merged_subs.save(output_file, encoding='utf-8')
                print(f"Sous-titres fusionnés sauvegardés dans: {output_file}")
            
            return merged_subs
        except Exception as e:
            print(f"Erreur lors de la fusion des sous-titres: {str(e)}")
            if output_file and os.path.exists(input_file):
                # En cas d'échec, simplement copier le fichier d'entrée
                import shutil
                shutil.copy(input_file, output_file)
                print(f"Fichier d'origine copié à {output_file}")
                return pysrt.open(input_file, encoding='utf-8')
            raise
    
    def _join_subtitles(self, subtitle_texts):
        """Joindre les textes des sous-titres en préservant la structure"""
        if not subtitle_texts:
            return ""
        
        if len(subtitle_texts) == 1:
            return subtitle_texts[0]
        
        # Grouper par phrases ou unités logiques
        result_lines = []
        current_line = ""
        
        for text in subtitle_texts:
            text = text.strip()
            if not text:
                continue
                
            # Si le texte se termine par une ponctuation, c'est probablement une pensée complète
            if text[-1] in '.!?':
                # Si nous avons une ligne en cours, ajouter ce texte et l'ajouter aux résultats
                if current_line:
                    if not current_line.endswith(" "):
                        current_line += " "
                    current_line += text
                    result_lines.append(current_line)
                    current_line = ""
                else:
                    # C'est une phrase autonome complète
                    result_lines.append(text)
            else:
                # C'est un fragment, l'ajouter à la ligne en cours
                if current_line:
                    if not current_line.endswith(" "):
                        current_line += " "
                    current_line += text
                else:
                    current_line = text
        
        # Ajouter tout texte restant
        if current_line:
            result_lines.append(current_line)
            
        # Joindre avec des sauts de ligne pour maintenir la structure des sous-titres
        return '\n'.join(result_lines)
    
    def translate_srt_file(self, input_file, output_file, batch_size=10, merge_duplicates=False, filter_noise=False):
        """Traduire un fichier SRT de l'anglais vers le français"""
        try:
            # Prétraitement si nécessaire
            source_file = input_file
            temp_files = []
            
            # Créer le répertoire de sortie s'il n'existe pas
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Filtrer les sous-titres de bruit si demandé
            if filter_noise:
                print("Filtrage des sous-titres de bruit...")
                temp_file = os.path.join(os.path.dirname(output_file), "temp_filter_" + os.path.basename(input_file))
                self.filter_noise_subtitles(input_file, temp_file)
                source_file = temp_file
                temp_files.append(temp_file)
            
            # Fusionner les sous-titres dupliqués si demandé
            if merge_duplicates:
                print("Fusion des sous-titres dupliqués...")
                temp_file = os.path.join(os.path.dirname(output_file), "temp_merge_" + os.path.basename(input_file))
                self.merge_duplicate_subtitles(source_file, temp_file)
                source_file = temp_file
                temp_files.append(temp_file)
            
            # Charger le fichier
            print(f"Chargement du fichier {source_file}...")
            subs = pysrt.open(source_file, encoding='utf-8')
            
            # Extraire le texte de chaque sous-titre
            texts = [sub.text for sub in subs]
            
            # Traduire tous les textes
            translated_texts = self.translate_batch(texts, batch_size)
            
            # Créer un nouveau fichier SRT avec les traductions
            translated_subs = pysrt.SubRipFile()
            for i, (sub, translated_text) in enumerate(zip(subs, translated_texts)):
                new_sub = pysrt.SubRipItem()
                new_sub.index = sub.index
                new_sub.start = sub.start
                new_sub.end = sub.end
                new_sub.text = translated_text
                translated_subs.append(new_sub)
            
            # S'assurer que le répertoire existe et sauvegarder le fichier traduit
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            translated_subs.save(output_file, encoding='utf-8')
            
            # Vérifier que le fichier a été créé
            if not os.path.exists(output_file):
                print(f"Attention: Le fichier n'a peut-être pas été sauvegardé correctement à {output_file}")
            else:
                print(f"Vérifié: Fichier sauvegardé à {output_file} ({os.path.getsize(output_file)} octets)")
            
            # Nettoyer les fichiers temporaires
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass  # Ignorer les erreurs de suppression de fichiers temporaires
            
            print(f"Traduction terminée. Fichier sauvegardé: {output_file}")
            return True
            
        except Exception as e:
            print(f"Erreur pendant la traduction: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def summarize_srt_file(self, input_file, max_length=None):
        """Génère un résumé du contenu d'un fichier SRT
        
        Args:
            input_file (str): Chemin vers le fichier SRT
            max_length (int, optional): Longueur maximale pour l'extraction de texte. Par défaut None (tout le texte).
        
        Returns:
            dict: Dictionnaire contenant le résumé et les informations sur le fichier
        """
        try:
            print(f"Chargement du fichier {input_file} pour résumé...")
            subs = pysrt.open(input_file, encoding='utf-8')
            
            # Extraction des informations de base
            total_subs = len(subs)
            duration_ms = subs[-1].end.ordinal if total_subs > 0 else 0
            duration_minutes = duration_ms / 60000
            
            # Extraire tout le texte (ou limité si max_length spécifié)
            all_text = " ".join([sub.text for sub in subs])
            if max_length and len(all_text) > max_length:
                all_text = all_text[:max_length] + "..."
            
            # Récupérer quelques exemples de sous-titres (début, milieu, fin)
            sample_subs = []
            if total_subs > 0:
                indices = [0]  # Début
                if total_subs > 2:
                    indices.append(total_subs // 2)  # Milieu
                if total_subs > 1:
                    indices.append(total_subs - 1)  # Fin
                
                for idx in indices:
                    sample_subs.append({
                        "index": subs[idx].index,
                        "start": str(subs[idx].start),
                        "end": str(subs[idx].end),
                        "text": subs[idx].text
                    })
            
            # Générer un résumé avec Ollama
            summary = ""
            if all_text:
                print("Génération du résumé du fichier...")
                summary = self._generate_summary_with_extended_timeout(all_text[:5000])
            
            # Préparer les résultats
            result = {
                "filename": os.path.basename(input_file),
                "subtitle_count": total_subs,
                "duration_minutes": round(duration_minutes, 2),
                "summary": summary,
                "sample_subtitles": sample_subs,
                "language_detected": self._detect_language(all_text[:500]) if all_text else "inconnu"
            }
            
            print(f"Résumé généré avec succès pour {input_file}")
            return result
            
        except Exception as e:
            print(f"Erreur lors de la génération du résumé: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "filename": os.path.basename(input_file),
                "error": str(e),
                "summary": "Impossible de générer un résumé"
            }
    
    def _generate_summary_with_extended_timeout(self, text):
        """Génère un résumé avec un timeout étendu et plusieurs tentatives
        
        Cette méthode utilise un temps d'attente beaucoup plus long et une stratégie de repli
        en cas d'échec pour garantir qu'un résumé sera généré même pour des textes longs.
        """
        if not text:
            return "Impossible de générer un résumé (texte vide)"
            
        # Limiter la longueur pour éviter les problèmes
        if len(text) > 5000:
            text = text[:5000] + "..."
            
        # Essayer avec un texte complet d'abord
        long_prompt = f"""
        Résume en français le contenu de cette vidéo en 3-5 phrases. Voici la transcription des sous-titres:
        
        {text}
        
        Résumé concis EN FRANÇAIS (maximum 3-5 phrases):
        """
        
        # Essayer avec un timeout très long (3 minutes)
        try:
            print("Tentative de résumé avec le texte complet et un délai étendu...")
            # Utiliser directement l'API Ollama avec un timeout personnalisé pour les résumés
            import requests
            import time
            
            timeout = 240  # 4 minutes de timeout pour les résumés
            
            start_time = time.time()
            payload = {
                "model": self.translator.model_name,
                "prompt": long_prompt,
                "stream": False,
                "temperature": 0.1,
                "num_predict": 300
            }
            
            print(f"Envoi de la requête de résumé avec timeout={timeout}s")
            response = requests.post(
                self.translator.api_url, 
                json=payload, 
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("response", "").strip()
                return self._clean_summary(summary)
        except Exception as e:
            print(f"Erreur lors de la génération du résumé complet: {str(e)}")
        
        # En cas d'échec, essayer avec un extrait plus court
        try:
            print("Tentative de résumé avec un extrait plus court...")
            shorter_text = text[:1500]  # Prendre seulement le début
            shorter_prompt = f"""
            Résume en français cette transcription de vidéo en 2-3 phrases. Voici l'extrait de la transcription:
            
            {shorter_text}
            
            Résumé très concis EN FRANÇAIS (2-3 phrases seulement):
            """
            
            # Utiliser la méthode standard de traduction avec un timeout standard
            summary = self.translator.translate(shorter_prompt)
            return self._clean_summary(summary)
        except Exception as e:
            print(f"Erreur lors de la génération du résumé court: {str(e)}")
        
        # Solution de dernier recours - traduire explicitement en français
        try:
            # Si nous avons échoué avec les méthodes précédentes, essayons de traduire directement
            word_count = len(text.split())
            sentences = text.split('.')[:5]  # Prendre les 5 premières phrases
            first_sentence = sentences[0].strip() if sentences else ""
            
            basic_summary = ""
            if first_sentence:
                basic_summary = f"Cette vidéo contient environ {word_count} mots. Elle commence par: \"{first_sentence}...\""
            else:
                basic_summary = f"Cette vidéo contient environ {word_count} mots."
                
            # Essayer de traduire directement ce résumé en français
            translation_prompt = f"Traduis ce texte en français: {basic_summary}"
            return self.translator.translate(translation_prompt)
        except:
            return "Impossible de générer un résumé pour cette vidéo. Le texte est peut-être trop long ou complexe."
    
    def _ensure_french_text(self, text):
        """Vérifie si le texte est en français et le traduit si nécessaire"""
        if not text or len(text) < 20:
            return text
            
        # Détection rapide basée sur les mots courants
        language = self._detect_language(text)
        
        # Si c'est déjà en français ou inconnu, on retourne le texte tel quel
        if language == "français" or language == "inconnu":
            return text
            
        # Si on détecte de l'anglais, on traduit
        if language == "anglais" or language == "anglais (probable)":
            print("Le résumé généré est en anglais. Traduction en français...")
            translation_prompt = f"Traduis ce texte en français: {text}"
            try:
                return self.translator.translate(translation_prompt)
            except Exception as e:
                print(f"Erreur lors de la traduction du résumé: {str(e)}")
                return f"[Résumé en anglais] {text}"
                
        return text
    
    def _clean_summary(self, summary):
        """Nettoie le résumé généré"""
        if not summary:
            return ""
            
        # Nettoyer le résumé (enlever les préfixes comme "Résumé:" etc.)
        prefixes = [
            "Résumé:", "Résumé concis:", "Voici le résumé:", "Le résumé est:",
            "Résumé très concis:", "En résumé:"
        ]
        for prefix in prefixes:
            if summary.lower().startswith(prefix.lower()):
                summary = summary[len(prefix):].strip()
                
        # Si le résumé commence par des guillemets, les enlever
        summary = summary.strip('"').strip()
        
        # S'assurer que le résumé est bien en français
        summary = self._ensure_french_text(summary)
                
        return summary
    
    def _detect_language(self, text):
        """Détecte la langue du texte de manière simple et rapide"""
        if not text:
            return "inconnu"
            
        # Mots fréquents en anglais
        english_words = ["the", "and", "of", "to", "a", "in", "that", "it", "with", "is", "was", "for", "on", "you", "are"]
        # Mots fréquents en français
        french_words = ["le", "la", "les", "un", "une", "des", "et", "est", "que", "qui", "dans", "pour", "avec", "ce", "au", "en"]
        
        text_lower = text.lower()
        
        # Compter les mots indicateurs
        english_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
        french_count = sum(1 for word in french_words if f" {word} " in f" {text_lower} ")
        
        # Détection simple basée sur le nombre de mots indicateurs trouvés
        if english_count > french_count:
            return "anglais"
        elif french_count > english_count:
            return "français"
        else:
            # Vérifier les caractères accentués comme indicateur supplémentaire
            accented_chars = sum(1 for c in text if c in "éèêëàâäôöùûüÿçÉÈÊËÀÂÄÔÖÙÛÜŸÇ")
            if accented_chars > 5:
                return "français"
            else:
                return "anglais (probable)"

def main():
    if len(sys.argv) < 3:
        print("Usage: python srt_translator.py <input_file.srt> <output_file.srt> [batch_size] [merge_duplicates] [filter_noise]")
        print("  batch_size: nombre de sous-titres par lot (par défaut: 10)")
        print("  merge_duplicates: 1 pour fusionner les doublons, 0 sinon (par défaut: 0)")
        print("  filter_noise: 1 pour filtrer les sous-titres de bruit, 0 sinon (par défaut: 0)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    merge_duplicates = bool(int(sys.argv[4])) if len(sys.argv) > 4 else False
    filter_noise = bool(int(sys.argv[5])) if len(sys.argv) > 5 else False
    
    translator = SRTTranslator()
    success = translator.translate_srt_file(input_file, output_file, batch_size, merge_duplicates, filter_noise)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 