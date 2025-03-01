<div align="center">
  <img src="https://github.com/LucaStrano/PaperSage/blob/main/.github/papersage_logo.png?raw=true" alt="PaperSage Logo"/>
</div>

# 🏠 Overview

📚 PaperSage is a Multi-Modal Chatbot designed to assist users in comprehending scientific papers. Leveraging Multi-Modal Language Models, PaperSage helps break down complex scientific concepts, answering questions, providing summaries, and highlighting key points within research papers. <br>
✨ Whether you’re a student, a researcher, or just someone who likes to read papers, This tool offers an interactive way to navigate and understand scientific literature.

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

To run the project, simply use the following command:

```bash
make run
```

# 📝 License

This project is licensed under the MIT License.