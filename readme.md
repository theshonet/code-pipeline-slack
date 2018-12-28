Code Pipeline Slack Bot
=======================

This bot will notify you of CodePipeline progress (using [CloudWatch Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html)).

We attempt to provide a unified summary, by pulling together multiple events, as well as information obtained by the API into a single message view.

![Build](build.gif)

### Fork changes ###
 - fixed issues (original code gave errors, slack api updates + code issues)
 - private channels support added

## Configuration / Customization

No configuration is necessary per pipeline.  As part of the CF Stack, we subscribe to all CodePipeline and CodeBuild events (using [CloudWatch Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html)).

When creating the CloudFormation stack, you can customize:

- `SlackChannel` (defaults to `builds`).
- `SlackChannelType` (defaults to `public`).
- `SlackBotName` (defaults to `PipelineBuildBot`).
- `SlackBotIcon` (defaults to `:robot_face:` 🤖 ).

Additionally, you must provide slack OAuth tokens (check next section on how to get it)
- `SlackOAuthAccessToken` 
- `SlackBotUserOAuthAccessToken`

If you have the legacy integration token, just add that token to both fields.

### Slack configuration
- create an app (or use existing app)
- create a bot user (see [BotUsers](https://api.slack.com/bot-users) for creating a slack bot user with an OAuth token)
- specify following scopes on your slack application OAuth & Permissions page: 
    - `channels:history ` (to search messages in public channels)
    - `groups:history` (to search messages in private channels)
    - `bot` (ability to invite bot to channels)
- add bot user to the desired channel
- copy OAuth tokens into CloudFormation stack


## How it works

We utilize [CloudWatch Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) for CodePipline and CodeBuild to get notified of all status changes.

Using the notifications, as well as using the CodePipeline APIs, we are able to present a unified summary of your Pipeline and Build status.


### IAM permissions

As part of the deployment, we create an IAM policy for the bot lambda function of:

```
Policies:
  - AWSLambdaBasicExecutionRole
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - 'codepipeline:Get*'
          - 'codepipeline:List*'
        Resource: '*'
      - Effect: Allow
        Action:
          - 'codebuild:Get*'
        Resource: '*'
```

So we can retrieve information about all pipelines and builds.  See [template.yml](https://github.com/AndreyMarchuk/code-pipeline-slack/blob/master/template.yml) for more detail.
