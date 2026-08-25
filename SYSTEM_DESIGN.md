# System Design Write-Up

**Society Maintenance Tracker** — Lavish Dixit
**Live app:** https://society-maintenance-tracker-1el4.onrender.com

This write-up covers four core design decisions: the complaint history
model, overdue detection, photo handling, and the notification flow.

---

## 1. Complaint History Model

Each `Complaint` stores its *current* `status` and `priority` directly as
fields, so filtering and dashboard counts stay fast and simple (no joins
needed for the common case of "show me all Open complaints"). But the
requirement is a *full* history, not just the current state — so every
status change also appends a row to a separate `StatusLog` table, linked to
the complaint by foreign key.

`StatusLog` is treated as append-only: rows are created via a single
method, `Complaint.add_status_log(new_status, actor, note)`, which updates
the parent complaint's `status` field and creates the log entry in the same
call. Nothing in the app ever edits or deletes a `StatusLog` row. This gives
two properties for free: the complaint's current status is always readable
in O(1) without touching history, and the full audit trail (who changed
what, when, and why) is reconstructable at any time by ordering
`complaint.history.all()` by timestamp. The very first entry (status =
Open, note = "Complaint raised") is written at creation time, so a
complaint's history always starts from the moment it was filed, not from
the first admin action.

The alternative — storing only the latest status and no log — was rejected
because residents and admins both need to see the full history, and
without an append-only log, that information is destroyed on every update.
Storing history as JSON on the complaint itself was also considered, but a
proper foreign-keyed table allows indexing, filtering by actor, and
admin-panel visibility without any custom parsing.

## 2. Overdue Detection

Overdue status is **computed, not stored**. `Complaint.is_overdue` is a
Python property: if the complaint's status is Resolved it returns `False`
immediately; otherwise it compares `timezone.now() - created_at` against a
threshold read from `settings.OVERDUE_THRESHOLD_DAYS`, sourced from an
environment variable (default 5 days).

This was a deliberate trade-off. Storing an `is_overdue` boolean column
would let admin-list queries `ORDER BY` it directly in the database, but it
requires a scheduled job to flip the flag as time passes, or lazy updates
on every read anyway — extra moving parts for a value that is a pure
function of `created_at`, `status`, and one config value. Computing it on
the fly means changing the threshold takes effect instantly across every
complaint, with no migration or background job required, at the cost of
sorting happening in Python rather than SQL once results are fetched —
acceptable at the scale of a single society's complaint volume. The admin
list view fetches the filtered queryset, evaluates `is_overdue` per
complaint, and stable-sorts so overdue complaints float to the top while
everything else stays reverse chronological.

## 3. Photo Handling

Complaints support an optional photo via Django's `ImageField`. Locally,
files are written to `MEDIA_ROOT` on disk — simple, no external service
needed for development. In production, storage switches to Cloudinary (a
`USE_CLOUDINARY` flag swaps Django's `DEFAULT_FILE_STORAGE` to
`cloudinary_storage`'s backend) because Render's filesystem is ephemeral:
anything written to local disk is wiped on every redeploy or restart, which
would silently delete resident-submitted evidence photos. Cloudinary's free
tier is enough for a single society's volume and needs no code change in
views or templates — only the storage backend changes, so
`complaint.photo.url` keeps working identically in both environments.

## 4. Notification Flow

Two events trigger email: a complaint's status changing, and an important
notice being posted. Both go through a single module
(`complaints/emails.py`) that all other apps call, so the logic isn't
duplicated.

Email is sent as a direct HTTPS call to **Brevo's HTTP API**
(`requests.post` to `api.brevo.com/v3/smtp/email`, authenticated with an
API key) rather than through Django's SMTP email backend. This was chosen
over SMTP because outbound SMTP ports are commonly blocked or throttled on
free hosting tiers, while a plain HTTPS request has no such restriction —
and over alternatives like SendGrid (60-day free trial only) and Resend
(cannot email arbitrary recipients without a verified custom domain),
because Brevo's free tier sends to any verified sender's real audience
indefinitely, with no domain required.

Emails are fire-and-forget from the request's point of view: the send
function wraps the API call in a `try/except` and only logs on failure, so
a temporary email-provider outage never turns into a failed request for
the resident or admin performing the action — the status update or notice
post itself always succeeds even if the email doesn't go out. Resolution
photos are base64-encoded and attached to the same API payload when a
complaint is marked Resolved, so a resident receives both the status change
and visual proof of completion in one email, with no separate delivery
step.
