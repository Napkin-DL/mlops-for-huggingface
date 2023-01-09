import json
from pprint import pprint
from sagemaker.workflow.pipeline import Pipeline

import boto3
client = boto3.client('sagemaker')


def exec_pipelines(pipeline_name, role, test_parameters_list, test_steps_list):
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=test_parameters_list,
        steps=test_steps_list,
    )
    pipeline.upsert(role_arn=role)
    # print("\n ********* The Definition of the Steps *********")
    # print(json.dumps(json.loads(pipeline.definition()), indent=4))
    # print("***********************************************")
    
    execution = pipeline.start()
    
    return execution


def describe_pipelines(execution):
    print('Pipelines Status : {} \n'.format(execution.describe()['PipelineExecutionStatus']))
    # print(execution.list_steps())
    for step in execution.list_steps():
        print('- StepName : {}, StepStatus : {}'.format(step['StepName'], step['StepStatus']))
        if step.get('CacheHitResult') : 
            print('- CacheHitResult : {} \n'.format(step['CacheHitResult']))
    

def get_step_results(execution, test_steps_list):
    exec_result = execution.list_steps()
    step_job_names = {}
    for step_result in exec_result:
        # print(step_result['Metadata'].keys())
        metadata = step_result['Metadata']
        for key_name in metadata.keys():
            key = filter_keyname(key_name)
            metadata_key_name = metadata[key_name]
            if key_name in ['ProcessingJob', 'TrainingJob']:
                val = metadata_key_name['Arn'].split('/')[-1]
            elif key_name in ['Condition']:
                val = metadata_key_name['Outcome']
            elif key_name in ['RegisterModel']:
                val = metadata_key_name['Arn'].split('/')[-2]+"/" + metadata_key_name['Arn'].split('/')[-1]
            step_job_names[key] = val
    
    pprint(step_job_names)
    
    for step_obj in test_steps_list:
        step_name = step_obj.step_type.value
        if step_name == 'Processing':
            step_job_name = step_job_names[step_name]
            res = client.describe_processing_job(ProcessingJobName=step_job_name)
            print(f"{step_name} : {step_job_name}")
            pprint(res['ProcessingOutputConfig']['Outputs'])
            print("\n --------------------------------------------------\n")
        elif step_name == 'Training':
            step_job_name = step_job_names[step_name]
            res = client.describe_training_job(TrainingJobName=step_job_name)
            print(f"{step_name} : {step_job_name}")
            print("S3ModelArtifacts : {}".format(res['ModelArtifacts']['S3ModelArtifacts']))
            print("\n --------------------------------------------------\n")
        elif step_name == 'Condition':
            step_job_name = step_job_names[step_name]
            print(f"{step_name} : {step_job_name}")
            print("\n --------------------------------------------------\n")
            

    if 'RegisterModel' in step_job_names.keys():
        step_job_name = step_job_names['RegisterModel']
        print(f"RegisterModel : {step_job_name}")
        print("\n --------------------------------------------------\n")

            
def filter_keyname(key_name):
    key_name = key_name.replace('Job', '')
    return key_name