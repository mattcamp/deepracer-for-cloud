# Continuous evaluation with InfluxDB metrics

This script runs a constant loop of evaluations, separate from the training. 

This allows for testing things like 3-lap trials with flying laps. 

The results of each evaluation are parsed and several metrics are pushed into InfluxDB for display on a grafana dashboard.

The fastest checkpoints are also copied to a new `fast_models` subdir within the original model folder, with a filename format of `checkpointNumber_averageLapTime_bestLapTime`


## How to use

Set up the `DR_EVAL_*` params in `run.env` to configure your evaluation environment.

```
cd utils/continuous_eval
dr-update
source eval_loop.sh
```

To stop ctrl-C a few times. 

To restart on a new model just re-run `dr-update` then `source eval_loop.sh` should begin testing the new model. 

It's a good idea to run it inside a `screen` or `tmux` session. 

NOTE: This currently doesn't store best-lap history per model so you'll probably want to remove the history.json file when you start training on a new track.