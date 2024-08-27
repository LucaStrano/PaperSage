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
- Docker ([Desktop](https://www.docker.com/products/docker-desktop/)) & Docker compose;
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
PaperSage expects an environment file named `.env` inside the project's root directory. This repo comes with an example env file named `.ex_env` which already contains the necessary environment variables, along with some predefined values. Please refer to the [Environment Variables Section](#environment-variables) to correctly setup your env variables. After you have finished modifying the `.ex_env` file, run:

```bash
mv .ex_env .env # rename environment file
```

To complete the installation, make sure that your `Docker service` is active and run the following inside the project's root directory:

```bash
make install
```

This will automatically install needed python modules, build all docker containers and run necessary setup scripts. For a list of all possible commands, you can always write:

```bash
make help
```

# Usage

TODO :)

# Environment Variables

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Postgres config variables. You can leave them as they are if you are not worried about security. if you already have a Postgres container running prior to PaperSage's installation, modify them accordingly. 