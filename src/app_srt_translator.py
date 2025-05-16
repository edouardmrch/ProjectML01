#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import streamlit as st
import tempfile
import pysrt
import time
import requests
import re

# Configuration de la page
st.set_page_config(
    page_title="SRT Translator",
    page_icon="🎬",
    layout="wide"
)

# Cacher les menus et barre d'outils de Streamlit
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    div.stToolbar {display: none;}
    div.stDecoration {display: none;}
    .reportview-container {
        margin-top: -2em;
    }
    .stDeployButton {display:none;}
    section[data-testid="stSidebar"] button[aria-expanded="true"] {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# CSS personnalisé pour améliorer l'interface
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: #1E88E5;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        color: #546E7A;
    }
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    .batch-counter {
        text-align: center;
        padding: 0.5rem;
        background-color: #E3F2FD;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-size: 1.1rem;
        font-weight: 500;
        color: #000000;
    }
    .progress-stats {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #000000;
    }
    .stat-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #F5F5F5;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5E9;
        margin-bottom: 1rem;
        text-align: center;
    }
    .summary-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5FD;
        margin: 1rem 0;
        border-left: 4px solid #1976D2;
    }
    .summary-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        color: #1565C0;
    }
    .summary-content {
        font-size: 1rem;
        line-height: 1.5;
        color: #333333;
    }
    .sample-subtitle {
        padding: 0.5rem;
        margin: 0.5rem 0;
        background-color: #F5F5F5;
        border-radius: 0.3rem;
        font-family: monospace;
    }
    .info-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin-right: 0.5rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        background-color: #E3F2FD;
        color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.markdown('<h1 class="main-title">🎬 Traducteur de Sous-titres SRT</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Traduction rapide et fiable de l\'anglais vers le français</p>', unsafe_allow_html=True)

# Vérifier la disponibilité d'Ollama
def check_ollama(host="localhost", port=11434):
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=10)
        return response.status_code == 200
    except:
        return False

# Traduire un fichier SRT
def translate_srt(input_file, output_file, model_name, batch_size=10, merge=False, filter=False):
    # Importer ici pour éviter le chargement séquentiel
    from srt_translator import SRTTranslator
    
    # Conteneurs pour le suivi de progression
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        progress_status = st.empty()
        subtitle_counter = st.empty()
    
    start_time = time.time()
    translator = SRTTranslator(model_name=model_name)
    
    # Compteurs de sous-titres
    total_subtitles = 0
    translated_subtitles = 0
    
    # Fonction pour mettre à jour la progression
    def update_progress(progress_value, batch_num=None, total_batches=None):
        progress_bar.progress(progress_value)
        
        elapsed = time.time() - start_time
        remaining = 0
        
        if progress_value > 0:
            remaining = (elapsed / progress_value) * (1 - progress_value)
        
        # Utiliser des valeurs sécurisées
        batch_display = batch_num if batch_num is not None else 0
        total_display = total_batches if total_batches is not None else 1
        
        status_html = f"""
        <div class="batch-counter">
            {batch_display}/{total_display} lots traités
        </div>
        <div class="progress-stats">
            <span>Temps écoulé: {elapsed:.1f}s</span>
            <span>Temps restant: {remaining:.1f}s</span>
        </div>
        """
        progress_status.markdown(status_html, unsafe_allow_html=True)
        
        if translated_subtitles > 0 and total_subtitles > 0:
            percentage = min(100, (translated_subtitles/total_subtitles)*100)
            subtitle_counter.markdown(f"""
            <div style="text-align: center; margin-top: 0.5rem;">
                {translated_subtitles}/{total_subtitles} sous-titres ({percentage:.0f}%)
            </div>
            """, unsafe_allow_html=True)
    
    # Démarrer à 0
    update_progress(0)
    
    # Sélectionner les messages importants
    import builtins
    original_print = builtins.print
    
    def custom_print(*args, **kwargs):
        text = ' '.join(map(str, args))
        nonlocal total_subtitles, translated_subtitles
        
        # Capturer le nombre total de sous-titres
        if "Traduction de " in text and "sous-titres" in text:
            count_match = re.search(r'Traduction de (\d+) sous-titres', text)
            if count_match:
                total_subtitles = int(count_match.group(1))
        
        # Chercher les informations de lot
        batch_match = re.search(r'Traitement du batch (\d+)/(\d+)', text)
        if batch_match:
            batch_num = int(batch_match.group(1))
            total_batches = int(batch_match.group(2))
            progress = (batch_num - 1) / total_batches
            update_progress(progress, batch_num, total_batches)
        
        # Chercher les informations de complétion
        if "✅ Batch" in text:
            batch_match = re.search(r'Batch (\d+)/(\d+)', text)
            if batch_match:
                batch_num = int(batch_match.group(1))
                total_batches = int(batch_match.group(2))
                progress = batch_num / total_batches
                trans_match = re.search(r'\((\d+)/(\d+)\)', text)
                if trans_match:
                    translated_subtitles = int(trans_match.group(1))
                    total_subtitles = int(trans_match.group(2))
                else:
                    translated_subtitles = int(total_subtitles * progress)
                update_progress(progress, batch_num, total_batches)
        
        # Chercher la fin de la traduction
        if "Traduction terminée" in text:
            update_progress(1.0, 1, 1)
        
        # Appeler la fonction d'origine
        original_print(*args, **kwargs)
    
    # Remplacer temporairement la fonction print
    builtins.print = custom_print
    
    try:
        # Exécuter la traduction
        success = translator.translate_srt_file(
            input_file, 
            output_file, 
            batch_size=batch_size, 
            merge_duplicates=merge, 
            filter_noise=filter
        )
        
        # Compléter la barre de progression
        update_progress(1.0, 1, 1)
        
        return success
    except Exception as e:
        print(f"Erreur de traduction: {str(e)}")
        return False
    finally:
        # Restaurer la fonction print
        builtins.print = original_print

# Analyser un fichier SRT
def analyze_srt_file(input_file, model_name):
    """Analyser et résumer un fichier SRT"""
    from srt_translator import SRTTranslator
    
    with st.spinner("Analyse du fichier en cours..."):
        translator = SRTTranslator(model_name=model_name)
        return translator.summarize_srt_file(input_file)

# Créer une mise en page à deux colonnes
col1, col2 = st.columns([2, 1])

# Configuration sidebar
st.sidebar.header("⚙️ Configuration")
host = st.sidebar.text_input("Serveur Ollama", "localhost")
port = st.sidebar.number_input("Port Ollama", min_value=1, max_value=65535, value=11434)

# Vérifier la connexion
ollama_available = check_ollama(host, port)
if ollama_available:
    st.sidebar.success("✅ Ollama est connecté")
    
    # Récupérer les modèles disponibles
    try:
        response = requests.get(f"http://{host}:{port}/api/tags", timeout=10)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            
            if models:
                # Préférer les modèles mistral ou llama
                preferred = [m for m in models if m.startswith(("mistral", "llama"))]
                default_model = preferred[0] if preferred else models[0]
                
                model_name = st.sidebar.selectbox(
                    "Modèle de Traduction", models, 
                    index=models.index(default_model) if default_model in models else 0
                )
            else:
                st.sidebar.warning("Aucun modèle trouvé. Veuillez en télécharger un d'abord.")
                model_name = st.sidebar.text_input("Nom du modèle", "mistral")
    except Exception as e:
        st.sidebar.warning(f"Impossible d'obtenir la liste des modèles: {e}")
        model_name = st.sidebar.text_input("Nom du modèle", "mistral")
else:
    st.sidebar.error("❌ Ollama n'est pas connecté")
    st.sidebar.markdown("""
    Assurez-vous qu'Ollama est installé et en cours d'exécution :
    1. Téléchargez-le depuis [ollama.com](https://ollama.com)
    2. Démarrez Ollama
    3. Téléchargez un modèle : `ollama pull mistral`
    """)
    model_name = "mistral"

# Réglages de performance
with st.sidebar.expander("⚡ Performances", expanded=True):
    batch_size = st.slider("Taille des lots", 1, 30, 10, 
                      help="Nombre de sous-titres traités à la fois. Des valeurs plus élevées sont plus rapides mais utilisent plus de mémoire.")
    
    st.markdown("""
    **Réglages recommandés :**
    - Petits fichiers (<100 sous-titres): Taille du lot 5-10
    - Fichiers moyens (100-500 sous-titres): Taille du lot 10-20
    - Grands fichiers (>500 sous-titres): Taille du lot 20-30
    """)

# Options avancées
with st.sidebar.expander("🔍 Options avancées"):
    merge_duplicates = st.checkbox("Fusionner les doublons", True,
                              help="Combine les sous-titres consécutifs similaires ou fragmentés")
    filter_noise = st.checkbox("Filtrer les sous-titres de bruit", True,
                          help="Supprime les sous-titres contenant uniquement [musique], [applaudissements], etc.")

with col1:
    # Interface principale de traduction
    uploaded_file = st.file_uploader("Téléchargez votre fichier SRT", type=["srt"])
    
    if uploaded_file:
        st.success(f"Fichier téléchargé : {uploaded_file.name}")
        
        try:
            # Lire le contenu du fichier pour afficher un aperçu
            file_content = uploaded_file.getvalue().decode("utf-8")
            sample_lines = file_content.split('\n')[:20]
            
            # Afficher un aperçu
            with st.expander("Aperçu du fichier", expanded=False):
                st.code('\n'.join(sample_lines) + "\n...", language="plaintext")
            
            # Créer des onglets pour la traduction et l'analyse
            tab1, tab2 = st.tabs(["🚀 Traduction", "📊 Résumé et Analyse"])
            
            with tab1:
                # Bouton pour démarrer la traduction
                translate_button = st.button("🚀 Traduire en français", type="primary", use_container_width=True)
                
                if translate_button:
                    if not ollama_available:
                        st.error("Ollama n'est pas connecté. Vérifiez votre installation.")
                    else:
                        with st.spinner("Traduction en cours..."):
                            # Enregistrer le fichier temporaire
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.srt') as temp_file:
                                temp_file.write(uploaded_file.getvalue())
                                input_path = temp_file.name
                            
                            # Configurer le chemin de sortie
                            output_dir = "srt-files-traduits"
                            os.makedirs(output_dir, exist_ok=True)
                            output_path = os.path.join(output_dir, f"fr_{uploaded_file.name}")
                            
                            # Démarrer le minuteur
                            start_time = time.time()
                            
                            # Démarrer la traduction
                            try:
                                # Exécuter la traduction
                                success = translate_srt(
                                    input_path, 
                                    output_path, 
                                    model_name,
                                    batch_size, 
                                    merge_duplicates,
                                    filter_noise
                                )
                                
                                if success and os.path.exists(output_path):
                                    # Afficher le temps d'exécution
                                    end_time = time.time()
                                    st.markdown(f'<div class="success-box">✅ Traduction terminée avec succès en {end_time - start_time:.2f} secondes !</div>', unsafe_allow_html=True)
                                    
                                    translation_container = st.container()
                                    with translation_container:
                                        try:
                                            # Lire le contenu du fichier traduit
                                            with open(output_path, 'r', encoding='utf-8') as f:
                                                content = f.read()
                                            
                                            # Afficher un aperçu du contenu traduit
                                            sample_lines = content.split('\n')[:20]
                                            with st.expander("Aperçu du fichier traduit", expanded=True):
                                                st.code('\n'.join(sample_lines) + "\n...", language="plaintext")
                                            
                                            # Bouton de téléchargement
                                            st.download_button(
                                                "📥 Télécharger le fichier traduit",
                                                content,
                                                file_name=f"fr_{uploaded_file.name}",
                                                mime="text/plain",
                                                use_container_width=True
                                            )
                                        except Exception as file_error:
                                            st.error(f"Erreur d'accès au fichier traduit : {str(file_error)}")
                                else:
                                    st.error("La traduction a échoué. Vérifiez les journaux.")
                            
                            except Exception as e:
                                st.error(f"Erreur : {str(e)}")
                            
                            # Nettoyer le fichier temporaire
                            try:
                                os.unlink(input_path)
                            except:
                                pass
            
            with tab2:
                # Bouton pour démarrer l'analyse et le résumé
                analyze_button = st.button("📝 Générer un résumé", type="primary", use_container_width=True)
                
                if analyze_button:
                    if not ollama_available:
                        st.error("Ollama n'est pas connecté. Vérifiez votre installation.")
                    else:
                        # Enregistrer le fichier temporaire
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.srt') as temp_file:
                            temp_file.write(uploaded_file.getvalue())
                            input_path = temp_file.name
                        
                        try:
                            # Lancer l'analyse
                            result = analyze_srt_file(input_path, model_name)
                            
                            if result:
                                # Afficher le résumé et les informations
                                st.markdown(f"""
                                <div class="summary-box">
                                    <div class="summary-title">📝 Résumé du contenu</div>
                                    <div class="summary-content">{result['summary']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Afficher les informations du fichier
                                info_col1, info_col2, info_col3 = st.columns(3)
                                with info_col1:
                                    st.markdown(f"""
                                    <div class="info-badge">🔤 Langue: {result['language_detected']}</div>
                                    """, unsafe_allow_html=True)
                                with info_col2:
                                    st.markdown(f"""
                                    <div class="info-badge">🔢 {result['subtitle_count']} sous-titres</div>
                                    """, unsafe_allow_html=True)
                                with info_col3:
                                    st.markdown(f"""
                                    <div class="info-badge">⏱️ {result['duration_minutes']} minutes</div>
                                    """, unsafe_allow_html=True)
                                
                                # Afficher des exemples de sous-titres
                                if result['sample_subtitles']:
                                    with st.expander("Exemples de sous-titres", expanded=False):
                                        for sample in result['sample_subtitles']:
                                            st.markdown(f"""
                                            <div class="sample-subtitle">
                                                <strong>{sample['start']} → {sample['end']}</strong><br>
                                                {sample['text']}
                                            </div>
                                            """, unsafe_allow_html=True)
                            else:
                                st.error("Impossible d'analyser le fichier. Veuillez réessayer.")
                        
                        except Exception as e:
                            st.error(f"Erreur lors de l'analyse : {str(e)}")
                        
                        finally:
                            # Nettoyer le fichier temporaire
                            try:
                                os.unlink(input_path)
                            except:
                                pass
        
        except Exception as e:
            st.error(f"Erreur de lecture du fichier : {str(e)}")

# Pied de page
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #757575; font-size: 0.8rem;">
    <p>Le Traducteur SRT utilise Ollama pour traduire des sous-titres de l'anglais vers le français.</p>
    <p>Pour de meilleures performances, utilisez le modèle Mistral.</p>
</div>
""", unsafe_allow_html=True) 