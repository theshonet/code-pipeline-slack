# -*- coding: utf-8 -*-

import json
import logging
from collections import OrderedDict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MessageBuilder(object):
    def __init__(self, build_info, message):
        self.buildInfo = build_info
        self.actions = []
        self.messageId = None

        if message:
            logger.info(json.dumps(message, indent=2))
            att = message['attachments'][0]
            self.fields = att['fields']
            self.actions = att.get('actions', [])
            self.messageId = message['ts']
            logger.info("Actions {}".format(self.actions))
        else:
            self.fields = [
                {"title": build_info.pipeline,
                 "value": "UNKNOWN",
                 "short": True
                 }
            ]

    def has_field(self, name):
        return len([f for f in self.fields if f['title'] == name]) > 0

    def needs_revision_info(self):
        return not self.has_field('Revision')

    def attach_revision_info(self, rev):
        if self.needs_revision_info() and rev:
            if 'revisionUrl' in rev:
                self.fields.append({
                    "title": "Revision",
                    "value": "<{}|{}: {}>".format(rev['revisionUrl'], rev['revisionId'][:7], rev['revisionSummary']),
                    "short": True
                })
            else:
                self.fields.append({
                    "title": "Revision",
                    "value": rev['revisionSummary'],
                    "short": True
                })

    def attach_logs(self, logs):
        self.find_or_create_action('Build Logs', logs['deep-link'])

    def find_or_create_action(self, name, link):
        for a in self.actions:
            if a['text'] == name:
                return a

        a = {"type": "button", "text": name, "url": link}
        self.actions.append(a)
        return a

    def pipeline_status(self):
        return self.fields[0]['value']

    def find_or_create_part(self, title, short=True):
        for a in self.fields:
            if a['title'] == title:
                return a

        p = {"title": title, "value": "", "short": short}
        self.fields.append(p)
        return p

    def update_build_stage_info(self, name, phases, info):
        url = info.get('latestExecution', {}).get('externalExecutionUrl')
        if url:
            self.find_or_create_action('Build dashboard', url)

        si = self.find_or_create_part(name, short=False)

        def pi(p):
            p_status = p.get('phase-status', 'IN_PROGRESS')
            return BUILD_PHASES[p_status]

        def fmt_p(p):
            msg = "{} {}".format(pi(p), p['phase-type'])
            d = p.get('duration-in-seconds')
            if d:
                return msg + " ({})".format(d)
            return msg

        def show_p(p):
            d = p.get('duration-in-seconds')
            return p['phase-type'] != 'COMPLETED' and d is None or d > 0

        def pc(p):
            ctx = p.get('phase-context', [])
            if len(ctx) > 0:
                if ctx[0] != ': ':
                    return ctx[0]
            return None

        context = [pc(p) for p in phases if pc(p)]

        if len(context) > 0:
            self.find_or_create_part("Build Context", short=False)['value'] = " ".join(context)

        pp = [fmt_p(p) for p in phases if show_p(p)]
        si['value'] = " ".join(pp)

    def update_status_info(self, stage_info, stage, status):
        sm = OrderedDict()

        if len(stage_info) > 0:
            for part in stage_info.split("\t"):
                (icon, sg) = part.split(" ")
                sm[sg] = icon

        icon = STATE_ICONS[status]
        sm[stage] = icon

        return "\t".join(['%s %s' % (v, k) for (k, v) in sm.items()])

    def update_pipeline_event(self, event):
        if event['detail-type'] == "CodePipeline Pipeline Execution State Change":
            self.fields[0]['value'] = event['detail']['state']

        if event['detail-type'] == "CodePipeline Stage Execution State Change":
            stage = event['detail']['stage']
            state = event['detail']['state']

            stageInfo = self.find_or_create_part('Stages')
            stageInfo['value'] = self.update_status_info(stageInfo['value'], stage, state)

    def color(self):
        return STATE_COLORS.get(self.pipeline_status(), '#eee')

    def message(self):
        return [
            {
                "fields": self.fields,
                "color": self.color(),
                "footer": self.buildInfo.executionId,
                "actions": self.actions
            }
        ]


# https://docs.aws.amazon.com/codepipeline/latest/userguide/detect-state-changes-cloudwatch-events.html
STATE_ICONS = {
    'STARTED': ":building_construction:",
    'SUCCEEDED': ":white_check_mark:",
    'RESUMED': "",
    'FAILED': ":x:",
    'CANCELED': ":no_entry:",
    'SUPERSEDED': ""
}

STATE_COLORS = {
    'STARTED': "#9E9E9E",
    'SUCCEEDED': "good",
    'RESUMED': "",
    'FAILED': "danger",
    'CANCELED': "",
    'SUPERSEDED': ""
}

# https://docs.aws.amazon.com/codebuild/latest/APIReference/API_BuildPhase.html
BUILD_PHASES = {
    'SUCCEEDED': ":white_check_mark:",
    'FAILED': ":x:",
    'FAULT': "",
    'TIMED_OUT': ":stop_watch:",
    'IN_PROGRESS': ":building_construction:",
    'STOPPED': ""
}
