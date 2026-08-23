# System Design Write-Up

## 1. Complaint History Model

Each `Complaint` stores its *current* `status` and `priority` directly as
fields, so filtering and dashboard counts stay fast and simple (no joins
needed for the common case of "show me all Open complaints"). But the
requirement is a *full* history, not just the current state — so every
status change also appends a row to a separate `StatusLog` table, linked to
the complaint by foreign key.

`StatusLog` is treated as append-only: rows are created via a single method,
`Complaint.add_status_log(new_status, actor, note)`, which updates the
parent complaint's `status` field and creates the log entry in the same
call. Nothing in the app ever edits or deletes a `StatusLog` row. This gives
two properties for free: the complaint's current status is always readable
in O(1) without touching history, and the full audit trail (who changed
what, when, and why) is reconstructable at any time by ordering
`complaint.history.all()` by timestamp. The very first entry (status =
Open, note = "Complaint raised") is written at creation time, so a
complaint's history always starts from the moment it was filed rather than
from the first admin action.

The alternative — storing only the latest status and no log — was rejected
because the assignment explicitly asks admins to see "what keeps coming
back" and residents to see full history; without an append-only log, that
information is destroyed on every update. Storing history as JSON on the
complaint itself was also considered, but a proper foreign-keyed table
allows indexing, filtering by actor, and admin-panel visibility without any
custom parsing.

## 2. Overdue Detection

Overdue status is **computed, not stored**. `Complaint.is_overdue` is a
Python property: if the complaint's status is Resolved it returns `False`
immediately; otherwise it compares `timezone.now() - created_at` against a
threshold read from `settings.OVERDUE_THRESHOLD_DAYS`, itself sourced from
an environment variable (`OVERDUE_THRESHOLD_DAYS`, default 5 days).

This was a deliberate trade-off. Storing an `is_overdue` boolean column
would make admin-list queries able to `ORDER BY` in the database directly,
but it requires either a scheduled job (cron/Celery beat) to flip the flag
as time passes, or updating it lazily on every read anyway — extra moving
parts for a value that is a pure function of `created_at`, `status`, and a
single config value. Computing it on the fly means changing the threshold
in the admin's settings takes effect instantly across every complaint, with
no migration or background job required, at the cost of sorting being done
in Python rather than SQL once results are fetched (acceptable at the scale
of a single society's complaint volume). The admin list view fetches the
filtered queryset, evaluates `is_overdue` per complaint, and stable-sorts so
overdue complaints float to the top while everything else stays reverse
chronological — matching the requirement that overdue items "surface at
the top of the admin view" without changing the underlying filter/date
logic.

## 3. Photo Handling

Complaints support one optional photo via Django's `ImageField`. Locally,
files are written to `MEDIA_ROOT` on disk — simple and requires no external
service for development or grading via `runserver`. In production, storage
switches to Cloudinary (a `USE_CLOUDINARY` flag in settings swaps Django's
`DEFAULT_FILE_STORAGE` to `cloudinary_storage`'s backend) because hosts
like Render and Railway use ephemeral filesystems: anything written to
local disk is wiped on every redeploy or restart, which would silently
delete resident-submitted evidence photos. Cloudinary's free tier is enough
for a single society's complaint volume and needs no code change in views
or templates — only the storage backend changes, so `complaint.photo.url`
keeps working identically in both environments.

## 4. Notification Flow

Two events trigger email: a complaint's status changing, and an important
notice being posted. Both go through a single small module
(`complaints/emails.py`) that wraps Django's `send_mail`, so both the
complaints app and the notices app call the same thin, already-tested
helper rather than duplicating SMTP logic.

Emails are fire-and-forget from the request's point of view: the
`_safe_send` helper wraps `send_mail` in a `try/except` and only logs on
failure, so a temporary SendGrid outage never turns into a 500 error for
the resident or admin performing the action — the status update or notice
post itself always succeeds even if the email doesn't go out. In local
development, the backend is Django's console backend, which prints the
email instead of sending it, so the full flow is verifiable without a real
SendGrid account. In production, the same code path uses SendGrid's SMTP
relay, configured entirely through environment variables (`SENDGRID_API_KEY`
as the SMTP password), so no application code changes between environments
— only configuration does.
