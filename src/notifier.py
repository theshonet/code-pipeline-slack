# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import boto3
import time
import logging

from pprint import pprint

from build_info import BuildInfo, CodeBuildInfo
from message_builder import MessageBuilder
from slack_helper import post_build_msg, find_message_for_build


logger = logging.getLogger()

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)


client = boto3.client('codepipeline')


def find_revision_info(info):
    r = client.get_pipeline_execution(
        pipelineName=info.pipeline,
        pipelineExecutionId=info.executionId
    )['pipelineExecution']

    revs = r.get('artifactRevisions', [])
    if len(revs) > 0:
        return revs[0]
    return None


# return (stageName, executionId, actionStateDict) if event executionId matches latest pipeline execution
def pipeline_from_build(code_build_info):
    r = client.get_pipeline_state(name=code_build_info.pipeline)

    for s in r['stageStates']:
        for a in s['actionStates']:
            execution_id = a.get('latestExecution', {}).get('externalExecutionId')
            if execution_id and code_build_info.buildId.endswith(execution_id):
                pe = s['latestExecution']['pipelineExecutionId']
                return s['stageName'], pe, a

    return None, None, None


def process_code_pipeline(event):
    if 'execution-id' not in event['detail']:
        logger.debug("Skipping due to no executionId")
        return

    build_info = BuildInfo.from_event(event)
    existing_msg = find_message_for_build(build_info)
    builder = MessageBuilder(build_info, existing_msg)
    builder.update_pipeline_event(event)

    if builder.needs_revision_info():
        revision = find_revision_info(build_info)
        builder.attach_revision_info(revision)

    post_build_msg(builder)


def process_code_build(event):
    if 'additional-information' not in event['detail']:
        logger.debug("Skipping due to no additional-information")
        return

    cbi = CodeBuildInfo.from_event(event)

    logger.debug(vars(cbi))

    (stage, pid, actionStates) = pipeline_from_build(cbi)

    logger.debug(stage, pid, actionStates)

    if not pid:
        return

    build_info = BuildInfo(pid, cbi.pipeline)

    existing_msg = find_message_for_build(build_info)
    builder = MessageBuilder(build_info, existing_msg)

    if 'phases' in event['detail']['additional-information']:
        phases = event['detail']['additional-information']['phases']
        builder.update_build_stage_info(stage, phases, actionStates)

    logs = event['detail'].get('additional-information', {}).get('logs')
    if logs:
        builder.attach_logs(event['detail']['additional-information']['logs'])

    post_build_msg(builder)


def process(event):
    if event['source'] == "aws.codepipeline":
        process_code_pipeline(event)
    if event['source'] == "aws.codebuild":
        process_code_build(event)


def run(event, context):
    logger.debug(json.dumps(event))
    process(event)


if __name__ == "__main__":
    with open('test-event.json') as f:
        events = json.load(f)
        for e in events:
            run(e, {})
            time.sleep(1)
