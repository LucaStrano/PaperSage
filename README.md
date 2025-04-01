<div align="center">
  <img src="https://github.com/LucaStrano/PaperSage/blob/main/.github/papersage_logo.png?raw=true" alt="PaperSage Logo"/>
</div>

# 🏠 Overview

📚 PaperSage is a Multi-Modal Chatbot designed to assist users in comprehending scientific papers. Leveraging Multi-Modal Language Models, PaperSage helps break down complex scientific concepts, answering questions, providing summaries, and highlighting key points within research papers. <br>
✨ Whether you’re a student, a researcher, or just someone who likes to read papers, This tool offers an interactive way to navigate and understand scientific literature. <br>
Features include:
- **Multi-Modal Interaction**: Ask questions about the paper and receive answers in text and images;
- **Custom Paper Processing**: Implements a custom PDF processing pipeline using [PaperMage](https://github.com/allenai/papermage) to extract text and images from papers with high precision and reduced artifacts;
- **Custom Metadata Extraction**: Extract custom metadata from paper chunks to improve retrieval and answer accuracy;
- **Lightweight and Fully Local**: PaperSage is designed to run locally on your machine, ensuring privacy and security. It does not strictly require any cloud services or external APIs. Papersage is also design to be lightweight and fast, with a small memory footprint. It can run on a standard laptop without the need for a powerful GPU.
- 
# 👨🏻‍💻 Installing

## Requirements

- Python;
- Anaconda ([MacOS](https://formulae.brew.sh/cask/anaconda)) or any other environment manager;
- Ollama ([MacOS](https://ollama.com));
- Make ([MacOS](https://formulae.brew.sh/formula/make)).

## Setup

Clone the repo using `git`:

```bash
git clone https://github.com/LucaStrano/PaperSage.git
cd PaperSage
```

This project was built using `Python 3.11.9`. It is recommended to use the same python version to avoid compatibilty issues. Use `Anaconda` to create a virtual environment:

```bash
conda create --name .papersage python=3.11
conda activate .papersage
```

Use `Make` to install the required dependencies:

```bash
make install
```

You can always use `make help` to see all available commands.

# 🚀 Running

To run the project, configure the `config.yaml`file with your custom settings. Standard settings are already provided and tested, and you can use them as a starting point. This project uses [LiteLLM](https://github.com/BerriAI/litellm) to interface with any custom provider/LLM. simply change the `model_name`config inside the `config.yaml` file to use your own provider/model. If you wish to use a cloud provider, be sure to export your API KEY before running the project.

After you have configured the `config.yaml` file, you can run the project using:

```bash
make run
```

# 🔮 Usage

Once the project is running, your default browser will open a new tab with the PaperSage interface. If you run the project for the first time, You will be asked to upload a PDF file. You can upload any scientific paper in PDF format. Once the processing is complete, you can start asking questions about the paper. If you have more papers, you can select the one you want to use from the settings menu (to the left of the chatbox). You can also upload a new paper at any time by providing a PDF to PaperSage.

You can use the `\img_search`command to ask PaperSage to provide an answer to your question while searching for an adeguate image. You can also provide a screenshot of an image of the paper. Follow-up questions are also supported.

# 📝 License

This project is licensed under the MIT License.