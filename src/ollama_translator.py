#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
from typing import List
import concurrent.futures
from tqdm import tqdm
import os

class OllamaTranslator:
    """Traducteur optimisé utilisant Ollama pour traduire de l'anglais vers le français"""
    
    def __init__(self, model_name: str = "mistral", host: str = "localhost", port: int = 11434):
        """Initialise le traducteur avec un modèle spécifique"""
        self.model_name = model_name
        self.api_url = f"http://{host}:{port}/api/generate"
        self.host = host
        self.port = port
        self.cache = {}  # Cache pour éviter de traduire plusieurs fois le même texte
        self.stats = {
            "requests": 0,
            "timeouts": 0,
            "errors": 0,
            "success": 0,
            "total_chars": 0,
            "total_time": 0
        }
        
        # Test de connexion
        self._test_connection()
    
    def _test_connection(self):
        """Teste la connexion au serveur Ollama"""
        try:
            response = requests.get(f"http://{self.host}:{self.port}/api/tags", timeout=10)
            if response.status_code != 200:
                print(f"Attention: Le serveur Ollama a retourné le code {response.status_code}")
            else:
                print(f"Connecté au serveur Ollama. Modèle: {self.model_name}")
        except Exception as e:
            print(f"Erreur de connexion à Ollama: {str(e)}")
            print("Assurez-vous qu'Ollama est en cours d'exécution et accessible.")
    
    def _log_stats(self, success=True, is_timeout=False, chars=0, time_taken=0):
        """Enregistre les statistiques de traduction pour diagnostiquer les problèmes"""
        self.stats["requests"] += 1
        if is_timeout:
            self.stats["timeouts"] += 1
        elif not success:
            self.stats["errors"] += 1
        else:
            self.stats["success"] += 1
            
        self.stats["total_chars"] += chars
        self.stats["total_time"] += time_taken
        
        # Afficher un résumé périodique
        if self.stats["requests"] % 10 == 0:
            success_rate = (self.stats["success"] / self.stats["requests"]) * 100 if self.stats["requests"] > 0 else 0
            avg_time = self.stats["total_time"] / self.stats["success"] if self.stats["success"] > 0 else 0
            print(f"📊 Statistiques: {self.stats['success']}/{self.stats['requests']} requêtes réussies ({success_rate:.1f}%), "
                  f"{self.stats['timeouts']} timeouts, {self.stats['errors']} erreurs. "
                  f"Temps moyen: {avg_time:.2f}s")
    
    def translate(self, text: str) -> str:
        """Traduit un texte anglais en français avec gestion de cache"""
        # Vérifier si le texte est vide
        if not text or text.strip() == "":
            return ""
        
        # Vérifier le cache
        if text in self.cache:
            return self.cache[text]
        
        # Prompt ultra-optimisé pour la traduction rapide
        prompt = f"""Traduis en français: {text}"""
        
        # Timeout beaucoup plus long pour éviter les erreurs de read timeout
        timeout = min(120, 30 + len(text) // 20)  # Timeout très généreux
        
        start_time = time.time()
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,  # Température basse pour des résultats plus déterministes
                "num_predict": min(200, len(text) * 2)  # Limite de prédiction pour accélérer
            }
            
            # Ajouter des logs pour diagnostiquer les problèmes de timeout
            print(f"Envoi de la requête avec timeout={timeout}s pour {len(text)} caractères")
            
            response = requests.post(self.api_url, json=payload, timeout=timeout)
            
            if response.status_code != 200:
                print(f"Erreur: L'API Ollama a retourné le code {response.status_code}")
                self._log_stats(success=False, chars=len(text), time_taken=time.time() - start_time)
                return text
            
            result = response.json()
            translation = result.get("response", "").strip()
            
            # Nettoyage basique et stockage en cache
            translation = self._clean_translation(translation)
            self.cache[text] = translation
            
            # Enregistrer les statistiques
            self._log_stats(success=True, chars=len(text), time_taken=time.time() - start_time)
            
            return translation
        except requests.exceptions.Timeout:
            time_taken = time.time() - start_time
            print(f"⚠️ Timeout lors de la traduction ({timeout}s) pour {len(text)} caractères. Temps écoulé: {time_taken:.1f}s.")
            self._log_stats(success=False, is_timeout=True, chars=len(text), time_taken=time_taken)
            return f"[Timeout après {timeout}s] {text[:50]}..." if len(text) > 50 else text
        except Exception as e:
            print(f"Erreur pendant la traduction: {str(e)}")
            self._log_stats(success=False, chars=len(text), time_taken=time.time() - start_time)
            # Retourner le texte d'origine en cas d'erreur
            return text
    
    def _clean_translation(self, translation: str) -> str:
        """Nettoie la traduction"""
        if not translation:
            return ""
        
        # Supprimer les préfixes courants
        prefixes = [
            "Voici la traduction :", 
            "Traduction :", 
            "En français :",
            "French translation:",
            "In French:",
            "Translation:",
            "Voici le texte traduit :",
            "La traduction est :",
            "Le texte traduit est :"
        ]
        
        for prefix in prefixes:
            if translation.lower().startswith(prefix.lower()):
                translation = translation[len(prefix):].strip()
        
        # Supprimer les guillemets si la traduction en est entourée
        translation = translation.strip('"').strip("'")
        
        return translation
    
    def translate_batch(self, texts: List[str], batch_size: int = 10) -> List[str]:
        """Traduit un lot de textes avec rapport de progression détaillé"""
        # Si la liste est vide, retourner une liste vide
        if not texts:
            return []
            
        # Vérifier le cache d'abord
        results = [""] * len(texts)
        to_translate = []
        indices = []
        
        # Identifier les textes qui ne sont pas dans le cache
        for i, text in enumerate(texts):
            if text in self.cache:
                results[i] = self.cache[text]
            else:
                to_translate.append(text)
                indices.append(i)
        
        # Si tout est déjà dans le cache, retourner les résultats
        if not to_translate:
            return results
        
        # Calculer le nombre de batches
        total_batches = (len(to_translate) + batch_size - 1) // batch_size
        
        print(f"Traduction de {len(to_translate)} sous-titres en {total_batches} batches...")
        
        # Fonction pour traduire un texte avec retries
        def translate_with_retry(text, retries=3, index=None):
            for attempt in range(retries + 1):
                try:
                    result = self.translate(text)
                    # Si le résultat commence par [Timeout après
                    if result.startswith("[Timeout après"):
                        if attempt < retries:
                            wait_time = 3 + attempt * 3
                            print(f"Nouvelle tentative après timeout. Attente de {wait_time}s... (tentative {attempt+1}/{retries+1})")
                            time.sleep(wait_time)
                            continue
                    return result
                except Exception as e:
                    if attempt < retries:
                        # Attente exponentielle entre les tentatives
                        wait_time = 2 + attempt * 3
                        print(f"Nouvelle tentative après erreur: {str(e)}. Attente de {wait_time}s... (tentative {attempt+1}/{retries+1})")
                        time.sleep(wait_time)
                    else:
                        print(f"Échec après {retries+1} tentatives: {str(e)}")
                        return f"[Erreur de traduction: {str(e)}]"
        
        # Traiter par petits groupes pour éviter les surcharges
        processed = 0
        with tqdm(total=len(to_translate), desc="Traduction", unit="sous-titre") as pbar:
            for i in range(0, len(to_translate), batch_size):
                current_batch = to_translate[i:i+batch_size]
                batch_indices = indices[i:i+batch_size]
                batch_num = i // batch_size + 1
                
                print(f"Traitement du batch {batch_num}/{total_batches} ({len(current_batch)} sous-titres)")
                
                # Mode ultra rapide pour les petits textes
                if all(len(text) < 100 for text in current_batch):
                    # Traitement séquentiel pour éviter la surcharge du serveur
                    for idx, text in enumerate(current_batch):
                        batch_idx = batch_indices[idx]
                        results[batch_idx] = translate_with_retry(text)
                        self.cache[text] = results[batch_idx]  # Mise à jour du cache
                        pbar.update(1)
                        processed += 1
                        # Petite pause entre chaque traduction pour donner du répit au serveur
                        if idx < len(current_batch) - 1:
                            time.sleep(0.2)
                else:
                    # Traitement spécial pour les textes longs (plus de 100 caractères)
                    long_texts = [idx for idx, text in enumerate(current_batch) if len(text) >= 200]
                    if long_texts:
                        print(f"Attention: {len(long_texts)} textes longs détectés dans ce lot. Traitement séquentiel pour éviter les timeouts.")
                        
                        # Traiter d'abord les textes longs séquentiellement avec plus de patience
                        for text_idx in long_texts:
                            text = current_batch[text_idx]
                            batch_idx = batch_indices[text_idx]
                            print(f"Traitement d'un texte long ({len(text)} caractères)...")
                            results[batch_idx] = translate_with_retry(text, retries=4)
                            self.cache[text] = results[batch_idx]
                            pbar.update(1)
                            processed += 1
                            # Pause plus longue après un texte long
                            time.sleep(0.5)
                    
                    # Traiter le reste des textes (moins longs) en parallèle
                    remaining_indices = [idx for idx in range(len(current_batch)) if idx not in long_texts]
                    if remaining_indices:
                        # Limiter encore plus le nombre de workers pour les textes restants
                        max_workers = min(2, len(remaining_indices))
                        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                            future_to_idx = {}
                            for idx in remaining_indices:
                                text = current_batch[idx]
                                batch_idx = batch_indices[idx]
                                future = executor.submit(translate_with_retry, text)
                                future_to_idx[future] = batch_idx
                            
                            for future in concurrent.futures.as_completed(future_to_idx):
                                batch_idx = future_to_idx[future]
                                text_idx = batch_indices.index(batch_idx)
                                orig_text = current_batch[remaining_indices[text_idx % len(remaining_indices)]]
                                try:
                                    results[batch_idx] = future.result()
                                    self.cache[orig_text] = results[batch_idx]
                                except Exception as e:
                                    results[batch_idx] = f"[Erreur: {str(e)}]"
                                pbar.update(1)
                                processed += 1
                
                # Sauvegarder les résultats intermédiaires
                print(f"✓ Batch {batch_num}/{total_batches} terminé ({processed}/{len(to_translate)})")
                
                # Pause entre les batches pour donner du répit au serveur
                if i + batch_size < len(to_translate):
                    time.sleep(0.2)
        
        return results

# Test simple si exécuté directement
if __name__ == "__main__":
    translator = OllamaTranslator()
    test_text = "Hello, how are you today?"
    translation = translator.translate(test_text)
    print(f"Original: {test_text}")
    print(f"Traduction: {translation}") 