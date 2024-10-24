SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
unset PYTHONHOME
python3 -m venv $SCRIPT_DIR/env
source $SCRIPT_DIR/env/bin/activate
pip install --upgrade pip
pip install -r $SCRIPT_DIR/${1}requirements.txt
