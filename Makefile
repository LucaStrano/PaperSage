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
	@echo "make run - Run PaperSage"
	@echo "make resetdb [id=PAPER_ID] - Reset Database (entire DB or specific paper)"


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
	@echo "🐍 installing Python Requirements, this may take a while..."
	@pip install -r requirements.txt > /dev/null || { echo "❌ Failed to Install Requirements. Aborting."; exit 1; }
	@echo "📦 initializing Database..."
	@python3 app/scripts/init_db.py || { echo "❌ Failed to Initialize Database. Aborting."; exit 1; }
	@echo "🦙 pulling Ollama embedding model..."
	@eval "$$(python3 app/scripts/read_config.py)" && ollama pull $$OLLAMA_EMB_MODEL || { echo "❌ Failed to Pull Ollama Embedding Model. Aborting."; exit 1; } 
	@echo "✅ PaperSage Installed Successfully."


.PHONY: run
run:
	@make banner
	@echo "\n\n"
	@echo "+---------------------------+"
	@echo "|  🚀 Running PaperSage...  |"
	@echo "+---------------------------+"
	@eval "$$(python3 app/scripts/read_config.py)" && ollama list && chainlit run --host $$CHAINLIT_HOST --port $$CHAINLIT_PORT main.py -w || { echo "❌ Failed to Run PaperSage. Aborting."; exit 1; }


.PHONY: resetdb
resetdb:
	@make banner
	@echo "\n\n"
	@echo "+---------------------------+"
	@echo "|  🔄 Resetting Database...  |"
	@echo "+---------------------------+"
	@if [ -z "$(id)" ]; then \
		read -p "🚨 This will clear all papers from the database. Are you sure? (y/N): " confirm && [[ $$confirm == [yY] || $$confirm == [yY][eE][sS] ]] || { echo "❌ Database reset cancelled."; exit 1; }; \
		python3 app/scripts/reset_db.py || { echo "❌ Failed to Reset Database. Aborting."; exit 1; }; \
		echo "📦 Rebuilding Database..."; \
		python3 app/scripts/init_db.py || { echo "❌ Failed to Initialize Database. Aborting."; exit 1; }; \
		echo "✅ Database Resetted Successfully."; \
	else \
		read -p "🚨 This will delete paper with ID $(id). Are you sure? (y/N): " confirm && [[ $$confirm == [yY] || $$confirm == [yY][eE][sS] ]] || { echo "❌ Paper deletion cancelled."; exit 1; }; \
		python3 app/scripts/reset_db.py $(id) || { echo "❌ Failed to Delete Paper. Aborting."; exit 1; }; \
		echo "✅ Paper $(id) Deleted Successfully."; \
	fi