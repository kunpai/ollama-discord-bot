ollama create chussu --file chussu.modelfile
ollama create kiwi --file kiwi.modelfile
ollama create babloo --file babloo.modelfile
python3 -m venv ./chussu
source ./chussu/bin/activate
pip3 install -r requirements.txt
