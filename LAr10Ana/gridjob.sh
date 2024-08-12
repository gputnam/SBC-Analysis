RUNDIR=$1
OUTDIR=$2
LOG="${CLUSTER}_${PROCESS}.log"
# LOG=/dev/stdout
OUT=output


echo "CONFIGURE ENVIRONMENT" >>${LOG} 2>&1
source /cvmfs/larsoft.opensciencegrid.org/products/setup >>${LOG} 2>&1
setup ifdhc v2_7 -q e26:p3915:prof >>${LOG} 2>&1

echo "INITIALIZE PYTHON VIRTUALENV"
source ${INPUT_TAR_DIR_LOCAL}/init.sh ${INPUT_TAR_DIR_LOCAL}/ >>${LOG} 2>&1
which python3 >>${LOG} 2>&1
python3 --version >>${LOG} 2>&1

export PYTHONPATH=$PYTHONPATH:${INPUT_TAR_DIR_LOCAL}
echo $PYTHONPATH

echo "COPY RUN TO LOCAL DIRECTORY"
LOCAL_RUNDIR=`basename $RUNDIR`
ifdh cp -r $RUNDIR $LOCAL_RUNDIR >>${LOG} 2>&1

echo "RUN EVENT DEALER" >>${LOG} 2>&1
python3 ${INPUT_TAR_DIR_LOCAL}/RunEventDealer.py ./$LOCAL_RUNDIR ./${OUT} >>${LOG} 2>&1

ifdh mkdir ${OUTDIR}/${CLUSTER}_${PROCESS}
ifdh cp -D ${LOG} ${OUT}/* ${OUTDIR}/${CLUSTER}_${PROCESS}/
ifdh_exit_code=$?

exit ${ifdh_exit_code}
