unset PYTHONHOME
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r ${1}requirements.txt
