import json
import argparse
import boto3
import os

from telegraf.client import TelegrafClient
tc = TelegrafClient(host='localhost', port=8092)

session = boto3.session.Session(profile_name='minio')

s3_client = session.client(
    service_name='s3',
    endpoint_url='http://192.168.0.5:9000',
)

s3_bucket=os.environ.get('DR_LOCAL_S3_BUCKET')


def s3_cp(src, dest):
    print(f"Copying {s3_bucket}/{src} -> {s3_bucket}/{dest}")
    res = s3_client.copy_object(Bucket=s3_bucket, 
                      CopySource=f"{s3_bucket}/{src}", 
                      Key=dest)
    # print(res)

parser = argparse.ArgumentParser(description='Process an eval')
parser.add_argument('-f', '--metrics_file', help='path to metrics json', required=True)
parser.add_argument('-c', '--checkpoint', help='name of the model checkpoint', required=True)
parser.add_argument('-m', '--model', help='name of the model', required=True)
args = parser.parse_args()

checkpoint=args.checkpoint
model = args.model

f = open(args.metrics_file)
metrics_data = json.load(f)
f.close


hf = open("history.json")
history = json.load(hf)
hf.close

total_resets = 0
total_time = 0
total_complete = 0
save = False
best_lap_time = 9999999999

for lap in metrics_data["metrics"]:
    # print(lap)
    total_resets += lap["reset_count"]
    total_time += lap["elapsed_time_in_milliseconds"]
    if lap["elapsed_time_in_milliseconds"] < best_lap_time:
        best_lap_time = lap["elapsed_time_in_milliseconds"]
        
    if int(lap["reset_count"]) > 0:
        clean_lap = "false"
    else:
        clean_lap = "true"
    tc.metric('laps', {'lap_time': lap["elapsed_time_in_milliseconds"], 'resets': lap["reset_count"]}, tags={'clean_lap': clean_lap, 'model': model, 'checkpoint': checkpoint})    
        
avg_time = round(total_time/3,0)
print(f"Total resets: {total_resets}\tTotal lap time: {total_time/1000}\tBest lap time: {best_lap_time/1000}\tAverage lap time: {round(avg_time/1000,3)}")


if int(total_resets) > 0:
    clean_run = "false"
else:
    clean_run = "true"
    
tc.metric('evals', {'best_laptime': best_lap_time, 'avg_laptime': avg_time, 'total_time': total_time, 'resets': total_resets}, tags={'clean_run': clean_run, 'model': model, 'checkpoint': checkpoint})

if best_lap_time < history['best_single_lap_time']:
    print(f"New best lap!")
    history['best_single_lap_time'] = best_lap_time
    history['best_single_lap_model'] = f"{model}/{checkpoint}"
    save = True
        
if total_time < history['best_total_time']:
    print("New best total time!")
    history['best_total_time'] = total_time
    history['best_total_model'] = f"{model}/{checkpoint}"  
    save = True 
    
if save:
    cp_num = checkpoint.split("_")[0]
    src_prefix = f"{model}/model"
    dst_prefix = f"{model}/fast_models/{cp_num}_a{avg_time}_b{best_lap_time}"
    
    print(f"Saving checkpoint to {dst_prefix}")
    
    s3_cp(src=f"{src_prefix}/{checkpoint}.index", dest=f"{dst_prefix}/{checkpoint}.index")
    s3_cp(src=f"{src_prefix}/{checkpoint}.data-00000-of-00001", dest=f"{dst_prefix}/{checkpoint}.data-00000-of-00001")
    s3_cp(src=f"{src_prefix}/{checkpoint}.meta", dest=f"{dst_prefix}/{checkpoint}.meta")
    s3_cp(src=f"{src_prefix}/deepracer_checkpoints.json", dest=f"{dst_prefix}/deepracer_checkpoints.json")
    s3_cp(src=f"{src_prefix}/model_metadata.json", dest=f"{dst_prefix}/model_metadata.json")
    s3_cp(src=f"{src_prefix}/model_{cp_num}.pb", dest=f"{dst_prefix}/model_{cp_num}.pb")

with open('history.json', 'w') as fp:
    json.dump(history, fp)


