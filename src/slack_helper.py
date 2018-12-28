from slackclient import SlackClient
import os
import json
import logging

sc = SlackClient(os.getenv("SLACK_TOKEN"))
sc_bot = SlackClient(os.getenv("SLACK_BOT_TOKEN"))
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "builds2")
SLACK_CHANNEL_TYPE = os.getenv("SLACK_CHANNEL_TYPE", "public")
SLACK_BOT_NAME = os.getenv("SLACK_BOT_NAME", "BuildBot")
SLACK_BOT_ICON = os.getenv("SLACK_BOT_ICON", ":robot_face:")
VERBOSE = os.getenv("VERBOSE", False)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if VERBOSE:
  logging.basicConfig()


CHANNEL_CACHE = {}

def find_channel(name):
  if name in CHANNEL_CACHE:
    return CHANNEL_CACHE[name]

  channel_type = 'private_channel' if SLACK_CHANNEL_TYPE.upper() == 'PRIVATE' else 'public_channel'

  r = sc_bot.api_call("conversations.list", exclude_archived=1, types=channel_type)
  if 'error' in r:
    logger.error("error getting channel with name '"+name+"': {}".format(r['error']))
  else:
      for ch in r['channels']:
        if ch['name'] == name:
          CHANNEL_CACHE[name] = (ch['id'], ch['is_private'])
          return CHANNEL_CACHE[name]
  
  return (None, None)

def find_msg(ch, is_private):
  method = 'groups.history' if is_private else 'channels.history'
  return sc.api_call(method, channel=ch)

def find_my_messages(ch_name, user_name=SLACK_BOT_NAME):
  ch_id, is_private = find_channel(ch_name)
  if not ch_id:
    logger.error("error getting channel")
    return
  
  print("Channel id = ", ch_id)
  msg = find_msg(ch_id, is_private)
  if 'error' in msg:
    logger.error("error fetching msg for channel {}: {}".format(ch_id, msg['error']))
  else:
    for m in msg['messages']:
      if m.get('username') == user_name:
        if VERBOSE:
          print("Found message: ", m)
        yield m

MSG_CACHE = {}

def find_message_for_build(buildInfo):
  cached = MSG_CACHE.get(buildInfo.executionId)
  if cached:
    return cached

  for m in find_my_messages(SLACK_CHANNEL):
    for att in msg_attachments(m):
      if att.get('footer') == buildInfo.executionId:
        MSG_CACHE[buildInfo.executionId] = m
        return m
  return None

def msg_attachments(m):
  return m.get('attachments', [])

def msg_fields(m):
  for att in msg_attachments(m):
    for f in att['fields']:
      yield f

def post_build_msg(msgBuilder):
  
  ch_id, is_private = find_channel(SLACK_CHANNEL)
  if VERBOSE:
    print("Channel id = ", ch_id)
  
  # update existing message
  if msgBuilder.messageId:
    
    msg = msgBuilder.message()
    if VERBOSE:
      print("Updating existing message")
    r = update_msg(ch_id, msgBuilder.messageId, msg)
    logger.info(json.dumps(r, indent=2))
    if r['ok']:
      r['message']['ts'] = r['ts']
      MSG_CACHE[msgBuilder.buildInfo.executionId] = r['message']
    return r
  
  if VERBOSE:
    print("New message")
  r = send_msg(ch_id, msgBuilder.message())
  #if r['ok']:
    # TODO: are we caching this ID?
    #MSG_CACHE[msgBuilder.buildInfo.executionId] = r['ts']
    #CHANNEL_CACHE[SLACK_CHANNEL] = (r['channel'], is_private)

  return r

def send_msg(ch, attachments):
  r = sc_bot.api_call("chat.postMessage",
    channel=ch,
    icon_emoji=SLACK_BOT_ICON,
    username=SLACK_BOT_NAME,
    attachments=attachments
  )
  return r

def update_msg(ch, ts, attachments):
  r = sc_bot.api_call('chat.update',
    channel=ch,
    ts=ts,
    icon_emoji=SLACK_BOT_ICON,
    username=SLACK_BOT_NAME,
    attachments=attachments
  )
  return r
