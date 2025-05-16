# SRT Subtitles Translator with LLMs

This project allows for automatic translation of SRT subtitle files from English to French, using Large Language Models (LLMs) via Ollama.

## Features

- Translation of SRT files from English to French with LLMs
- Summarization of SRT content to quickly understand video content
- User-friendly graphical interface with Streamlit
- Support for Mistral, Llama2, and other Ollama models
- Contextual analysis of subtitles to improve translation quality
- Optimization of prompts specific to each model
- Intelligent cleaning of model responses
- Progress bar and translation preview
- Support for all properly formatted SRT files
- Robust error handling for long texts and timeouts

## Detailed Streamlit Interface Guide

The application provides a rich interactive interface through Streamlit with various options and settings to customize the translation process.

### Main Interface

- **Title and Description**: The top of the page displays the application title and a brief description.
- **File Upload**: A file upload widget that accepts SRT files (`.srt` extension).
- **File Information**: Once a file is uploaded, it displays the file name and size.
- **Tab System**: Two tabs for Translation and Summary functionality.
- **Translation Tab**: Contains all translation-related features.
- **Summary Tab**: Contains features to analyze and summarize the content.
- **Translation Progress**: During translation, a progress bar and status text show the current progress.
- **Results Preview**: After translation, an expandable section shows a preview of the translated content.
- **Download Button**: A button to download the completed translation as an SRT file.

### Sidebar Configuration

- **Ollama Configuration**:
  - **Host**: Input field to set the Ollama host (default: localhost).
  - **Port**: Numeric field to set the Ollama port (default: 11434).
  - **Connection Status**: Visual indicator showing if Ollama is accessible.
  - **Model Selection**: Dropdown menu to select the translation model.

### Advanced Settings

The sidebar contains several important settings:

#### Performance Parameters

- **Batch Size**: Controls how many subtitles are processed in one group. Larger batch sizes speed up translation but may use more memory.

#### Subtitle Optimization

- **Merge Duplicates** (enabled by default): Combines consecutive subtitles that contain partial sentences or identical text. This improves readability by creating more coherent sentences when the original subtitles were split mid-sentence.

- **Filter Noise** (enabled by default): Removes subtitles that only contain non-speech information like [music], [applause], etc. It also cleans such indications from regular subtitles, resulting in cleaner translated text.

### Summary Feature

The summary tab provides an AI-generated summary of the SRT content:

- **Generate Summary Button**: Creates a concise summary of the video content.
- **Summary Box**: Displays the generated summary in French.
- **Content Information**: Shows language detection, subtitle count, and video duration.
- **Sample Subtitles**: Provides examples from the beginning, middle, and end of the subtitle file.

This feature is useful for quickly understanding the content without translating the entire file.

## Prerequisites

- Python 3.6+
- [Ollama](https://ollama.com/)
- pip (Python package manager)

## Installation

1. Install Ollama
   - On macOS/Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - On Windows: Download the installer from [ollama.com](https://ollama.com/)

2. Download the models for Ollama:
   ```bash
   ollama pull mistral  # Recommended for best quality
   ollama pull llama2   # Strong alternative
   ```

3. Clone or download this repository

4. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

5. Install dependencies:
   ```bash
   # Use the dependency resolution script if you encounter problems
   ./fix_dependencies.sh  # Linux/Mac
   # or
   fix_dependencies.bat  # Windows
   
   # Or standard installation
   pip install -r requirements.txt
   ```

## Project Structure

```
.
├── srt-files/          # Folder containing SRT files to translate
├── srt-files-traduits/ # Folder where translated files will be stored
├── src/
│   ├── app_srt_translator.py  # Main Streamlit application
│   ├── ollama_translator.py   # Integration module with Ollama
│   ├── srt_translator.py      # SRT file translation module
│   └── main.py                # Main script (command line version)
├── run_app.sh           # Script to launch the interface (Linux/Mac)
├── run_app.bat          # Script to launch the interface (Windows)
├── fix_dependencies.sh  # Script to resolve dependency issues (Linux/Mac)
├── fix_dependencies.bat # Script to resolve dependency issues (Windows)
├── requirements.txt     # Project dependencies
└── README.md
```

## Usage

### Graphical interface (recommended)

1. Make sure Ollama is running

2. Launch the Streamlit application:
   ```bash
   # On Linux/Mac
   ./run_app.sh
   
   # On Windows
   run_app.bat
   ```
   
   Or directly with Python:
   ```bash
   # Linux/Mac/Windows with Bash
   cd src && python -m streamlit run app_srt_translator.py
   
   # Windows with PowerShell
   cd src ; python -m streamlit run app_srt_translator.py
   ```
   
   You can also use this complete command from any directory:
   ```bash
   # Absolute path (adjust according to your installation)
   python -m streamlit run C:\path\to\project\src\app_srt_translator.py
   ```

3. Follow the instructions in the web interface to load and translate your SRT files

### Command line

1. Make sure Ollama is running

2. Place your SRT files in the `srt-files/` folder

3. Run the main script:
   ```bash
   python src/main.py
   ```

4. Translated files will be available in the `srt-files-traduits/` folder with the "fr_" prefix

To translate a specific file:
```bash
python src/srt_translator.py path/to/file.srt path/to/output.srt
```

## Model Selection

This project supports several language models through Ollama:

- **Mistral**: Recommended for the best translation quality
- **Llama2**: Good balance between quality and speed
- **Other Ollama models**: Any model available in your Ollama installation can be used

The prompts have been specifically optimized to obtain the best possible translations.

## Technical Optimizations

- **Contextual Analysis**: The system analyzes the entire SRT file to provide context to the model
- **Optimized Prompts**: Each model uses specific prompts to maximize translation quality
- **Intelligent Cleaning**: Model responses are cleaned of common artifacts
- **Error Handling**: The system handles network errors, timeouts, and automatically retries with different approaches
- **Extended Timeouts**: Long content processing has enhanced timeout handling
- **Language Detection**: Automatic verification that summaries are in French

## Troubleshooting

### Installation Issues

If you encounter problems when installing dependencies, use the provided scripts:

```bash
# On Linux/Mac
./fix_dependencies.sh

# On Windows
fix_dependencies.bat
```

These scripts install dependencies with special options to solve common problems.

### Issues with Ollama

- If Ollama is not detected, make sure the Ollama service is running
- On macOS/Linux: `systemctl status ollama` or restart with `systemctl restart ollama`
- On Windows: Check in the task manager that ollama.exe is running

- Verify that the model is downloaded:
  ```bash
  ollama list
  ```
- If the model is not listed, download it:
  ```bash
  ollama pull mistral
  ```

### Translation Quality

If you are not satisfied with the translation quality:

1. Try a different model (Mistral is recommended for the best quality)
2. Restart Ollama if you notice performance degradation
3. For long files, consider dividing them into smaller segments

### Timeout Errors

If you encounter timeout errors:
1. Reduce the batch size in the interface
2. Try a model that processes text faster
3. For summaries, the application will automatically try alternative approaches if the first attempt times out

## About This Project

This is a machine learning project created for the ML01 course. This project is openly available for reuse and modification. You are authorized to recycle, adapt, or build upon this project for your own purposes, whether academic or personal.

---

# Traducteur de Sous-titres SRT avec LLMs

*Version française résumée*

Ce projet permet la traduction automatique de fichiers de sous-titres SRT de l'anglais vers le français, en utilisant des modèles de langage (LLMs) via Ollama. L'interface graphique facilite le téléchargement, la traduction et le téléchargement des fichiers traduits.

## Fonctionnalités principales

- Traduction automatique des sous-titres de l'anglais vers le français
- Génération de résumés en français du contenu de la vidéo
- Interface utilisateur intuitive avec Streamlit
- Support pour plusieurs modèles d'IA via Ollama
- Analyse contextuelle pour améliorer la qualité des traductions
- Gestion avancée des erreurs et des timeouts
- Prévisualisation des traductions et barre de progression

Consultez la documentation en anglais ci-dessus pour les instructions d'installation et d'utilisation détaillées. 