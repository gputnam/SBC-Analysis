SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
unset PYTHONHOME
. $SCRIPT_DIR/env/bin/activate
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR/..
