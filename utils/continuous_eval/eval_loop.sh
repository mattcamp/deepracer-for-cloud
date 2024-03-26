set -x
while true
do
    LOOP_ID=$(date +%s)

    mkdir -p tmp

    LOGFILE1="./tmp/eval-${LOOP_ID}.log.1"
    LOGFILE2="./tmp/eval-${LOOP_ID}.log.2"
    MODEL=${DR_LOCAL_S3_MODEL_PREFIX}

    dr-stop-evaluation
    echo "Starting evaluation of ${MODEL}"
    dr-start-evaluation -c  2> ${LOGFILE2} 1> ${LOGFILE1}
    dr-stop-evaluation

    CHECKPOINT=$(grep checkpoint/agent/ ${LOGFILE1} | cut -d '/' -f 4)

    METRICS_PATH=$(grep "Successfully uploaded metrics" ${LOGFILE2} | xargs | cut -d ' ' -f 12)
    METRICS_PATH=${METRICS_PATH::-1}
    METRICS_FILE=$(echo ${METRICS_PATH} | cut -d '/' -f 3)

    dr-local-aws s3 cp s3://${DR_LOCAL_S3_BUCKET}/${METRICS_PATH} ./tmp/eval-${LOOP_ID}.json

    echo "Analysing eval ${MODEL}/${CHECKPOINT}"

    python3 ./analyse_eval.py -f ./tmp/eval-${LOOP_ID}.json -c ${CHECKPOINT} -m ${MODEL}

    rm ./tmp/eval-${LOOP_ID}.*
    dr-local-aws s3 rm --recursive s3://${DR_LOCAL_S3_BUCKET}/${MODEL}-E
done