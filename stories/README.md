# FABLAB PROJECT STORIES SCHEDULER

Asks members what they made on a machine, for the success stories on Made in FabLab.

Every run reads finished machine sessions from Fabman (`/resource-logs`) and picks members whose session on a
watched machine lasted at least `PROJECT_STORIES_MIN_MINUTES` (idle time left out). Each of them gets one email
through the bridge (`POST /project-story`) about their longest recent session, at most once per
`PROJECT_STORIES_COOLDOWN_DAYS`. The date of the last question is kept in the member's Fabman metadata
(`project_story_asked_at`), so the scheduler needs no database and a re-run never asks twice.

The email is an Ecomail transactional template with a link to a Google Form and reply-to set to a person,
so members can either fill the form or just answer the email.

It is a Railway cron service of its own, separate from `scheduler/` - stop it without touching the training
and booking tasks.

<br>

# FIRST RUN
1. Deploy with `SCHEDULED_TASK=list_resources` and read the log: machine and machine-type ids.
2. Set `PROJECT_STORIES_RESOURCE_TYPES` and/or `PROJECT_STORIES_RESOURCES`, switch to `SCHEDULED_TASK=project_stories`.
   `PROJECT_STORIES_DRY_RUN` is on by default: the log says who would be asked, nothing is sent or written.
3. Optionally `TEST_USER=<member id>` and dry run off, to send one real email to yourself.
4. Dry run off, `TEST_USER` removed, and `PROJECT_STORIES_SEND_EMAILS=true` on the bridge.

<br>

# DEPLOYMENT
Railway cron service with root directory `stories/`, e.g. schedule `0 * * * *` (hourly). Start command is in
**nixpacks.toml**.

<br>

## ENV VARIABLES:

Scheduler (this service):
* FABMAN_API_KEY: same value as in `scheduler/` (incl. `Bearer `)
* RAILWAY_API_URL: URL of bridge service
* CRONJOB_TOKEN: verification token for scheduler service
* SCHEDULED_TASK: `project_stories` (default) or `list_resources`
* PROJECT_STORIES_RESOURCE_TYPES: comma separated Fabman resource type ids (e.g. all 3D printers)
* PROJECT_STORIES_RESOURCES: comma separated Fabman resource ids
* PROJECT_STORIES_EXCLUDE_MEMBERS: comma separated member ids or e-mail addresses never asked (staff, people who
  replied they don't want these e-mails - they stay on the FabLab newsletters)
* PROJECT_STORIES_MIN_MINUTES: minimal active session length, default 20
* PROJECT_STORIES_COOLDOWN_DAYS: default 30
* PROJECT_STORIES_LOOKBACK_HOURS: how old a finished session may be, default 24
* PROJECT_STORIES_DRY_RUN: default `true` - log only
* TEST_USER: only this member's sessions

Bridge:
* ECOMAIL_TEMPLATE_ID_PROJECT_STORY: Ecomail transactional template
* PROJECT_STORIES_SEND_EMAILS: (boolean) default `false` - the bridge answers 503 and sends nothing
* PROJECT_STORIES_REPLY_TO: where replies go
* PROJECT_STORIES_SUBJECT: default `Co vzniklo na stroji {resource}?`
* PROJECT_STORIES_FORM_URL: Google Forms pre-filled link; `{email}`, `{member_id}`, `{resource}` and `{date}` are replaced

Template merge tags: `*|FIRST_NAME|*`, `*|RESOURCE|*`, `*|USED_ON|*`, `*|DURATION_MINUTES|*`, `*|FORM_URL|*`.
