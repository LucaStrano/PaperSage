#   ____                       ____                   
#  |  _ \ __ _ _ __   ___ _ __/ ___|  __ _  __ _  ___ 
#  | |_) / _` | '_ \ / _ \ '__\___ \ / _` |/ _` |/ _ \
#  |  __/ (_| | |_) |  __/ |   ___) | (_| | (_| |  __/
#  |_|   \__,_| .__/ \___|_|  |____/ \__,_|\__, |\___|
#             |_|                          |___/      
#
# Made By Luca Strano - https://github.com/LucaStrano

defaut: help

.PHONY: help
help:
	@make banner
	@echo "\n\n"
	@echo "+---------------+"
	@echo "|  🏠 COMMANDS  |"
	@echo "+---------------+"
	@echo "make install - Install PaperSage"
	@echo "make process - Process a Document with path DOC_PATH. Default is DOCS/"
	@echo "make cleandb - Clean and rebuild the Database (run with sudo)"

.PHONY: banner
banner:
	@echo "  ____                       ____                    "
	@echo " |  _ \ __ _ _ __   ___ _ __/ ___|  __ _  __ _  ___  "
	@echo " | |_) / _\` | '_ \ / _ \ '__\___ \ / _\` |/ _\` |/ _ \ "
	@echo " |  __/ (_| | |_) |  __/ |   ___) | (_| | (_| |  __/ "
	@echo " |_|   \__,_| .__/ \___|_|  |____/ \__,_|\__, |\___| "
	@echo "            |_|                          |___/       "
	@echo "+---------------------------------------------------+"
	@echo "|      https://github.com/LucaStrano/PaperSage      |"
	@echo "+---------------------------------------------------+"

.PHONY: install
install:
	@make banner
	@echo "\n\n"
	@echo "+------------------------------+"
	@echo "|  📦 Installing PaperSage...  |"
	@echo "+------------------------------+"
	@echo "🐍 installing Requirements..."
	@pip install -r requirements.txt || { echo "❌ Failed to Install Requirements. Aborting."; exit 1; }
	@mkdir -p app/postgres/data
	@mkdir -p DOCS
	@echo "🐋 Building Docker Containers..."
	@docker-compose build || { echo "❌ Failed to Build Docker Containers. Aborting."; exit 1; }

DOC_PATH ?= DOCS/
.PHONY: process
process:
	@make banner
	@echo "\n\n"
	@echo "+--------------------------------+"
	@echo "|  📄 Processing Document(s)...  |"
	@echo "+--------------------------------+"
	@python app/scripts/send_documents.py $(DOC_PATH)
#   Outputs delegated to send_documents.py

.PHONY: cleandb
cleandb:
	@make banner
	@echo "\n\n"
	@read -p "🚨 Are you sure you want to clean the Database? [y/n]: " confirm; \
	if [ "$$confirm" != "y" ]; then \
		echo "🚫 Aborted."; \
		exit 1; \
	fi
	@echo "+---------------------------+"
	@echo "|  🧹 Cleaning Database...  |"
	@echo "+---------------------------+"
	@docker-compose stop
	@rm -rf app/postgres/data
	@docker-compose up ps-postgres --build -d