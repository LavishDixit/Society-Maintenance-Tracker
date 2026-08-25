# 🏛️ Society Maintenance Tracker

A full-stack web platform for apartment societies to manage maintenance complaints
end to end — residents raise complaints with photos, the committee triages and
resolves them through a tracked workflow, and everyone stays informed through a
targeted notice board, a rules page, an emergency contacts directory, and email
alerts.

**🔗 Live app:** [society-maintenance-tracker-1el4.onrender.com](https://society-maintenance-tracker-1el4.onrender.com)

Built with **Django** (server-rendered templates + Bootstrap 5), **PostgreSQL
(Neon)**, **Cloudinary** for photo storage, and **Brevo** for transactional email.

---

## 1. Features

**Every account is a resident** (has a wing + flat number). Committee/admin
access is an *additional* permission (`is_committee`), not a separate account
type — a committee member can manage the society **and** raise complaints for
their own flat, without the two roles conflicting.

### Resident
- Register (wing + flat number required — this, not name, is the unique
  identifier, so two residents can safely share a name)
- Raise a complaint with category, description, and an optional photo
  (camera capture supported on mobile)
- View all their own complaints with the full status history of each
- Browse the notice board (only sees notices addressed to them — everyone,
  their wing, or personally)
- Read society rules & regulations
- Look up committee and emergency contact numbers

### Committee / Admin
- Everything a resident can do, **plus**:
- View all complaints; filter by category, status, date range, or free-text
  search (resident name, flat, description)
- Set complaint priority (Low / Medium / High)
- Update complaint status (Open → In Progress → Resolved); every change is
  recorded with a timestamp, actor, and optional note — a full audit trail,
  never overwritten
- Attach an "after" resolution photo when closing a complaint — it's emailed
  to the resident automatically
- Complaints open longer than a configurable threshold are flagged
  **Overdue** and surface at the top of the list, with a live count badge in
  the nav
- Post notices to the whole society, a specific wing, or a specific resident
- Mark a notice **Important** to pin it and trigger an email to the right
  audience (everyone / that wing / that resident)
- Manage Rules & Regulations (add/edit/delete)
- Manage Committee & Emergency Contacts (add/edit/delete)
- Searchable Resident Directory + CSV export
- Upload and archive reference documents (PDF/Word/Excel/CSV/images) —
  committee-only storage for official records
- Dashboard: total complaints, breakdown by status (doughnut chart),
  breakdown by category (bar chart), live overdue count

### System-wide
- Role-based access control throughout
- Email notifications on complaint resolution (with photo attachment when
  provided) and on important notices (sent only to the targeted audience)
- Photo lightbox, ink-stamp status badges, and a "civic register" visual
  design built for readability over decoration

---

## 2. Tech Stack

| Layer          | Choice                                             |
|----------------|-----------------------------------------------------|
| Backend        | Django 6.1                                          |
| Frontend       | Django Templates + Bootstrap 5 (server-rendered)    |
| Database       | PostgreSQL via [Neon](https://neon.tech) (SQLite for local dev) |
| Photo/file storage | [Cloudinary](https://cloudinary.com) (free tier)     |
| Email          | [Brevo](https://www.brevo.com) **HTTP API** (via `requests`) — not SMTP |
| Hosting        | [Render](https://render.com) (free tier web service) |
| Static files   | WhiteNoise                                          |
| Charts         | Chart.js (dashboard)                                |

---

## 3. Local Setup

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/LavishDixit/Society-Maintenance-Tracker.git
cd Society-Maintenance-Tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file
cp .env.example .env
# Defaults use local SQLite and local disk for photos - no external
# accounts needed just to run it locally. Email will only actually send if
# BREVO_API_KEY is set in .env; leave it blank locally and emails simply
# won't send (failures are logged, not fatal) - see section 9.

# 5. Run migrations
python manage.py migrate

# 6. Create an admin account
python manage.py createsuperuser

# then grant committee/admin access:
python manage.py shell -c "
from accounts.models import User
u = User.objects.get(username='<your-username>')
u.is_committee = True
u.save()
"

# 7. Run the dev server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — it redirects to the login page. Log in with
your admin account to see the full committee toolset, or sign up as a new
resident to try the resident flow.

Email sending is opt-in locally: if `BREVO_API_KEY` is left blank in `.env`,
`complaints/emails.py` will attempt the API call, it'll fail, and the
failure is caught and logged — the app keeps working normally, you just
won't see the email. Set `BREVO_API_KEY` (and a verified `DEFAULT_FROM_EMAIL`)
locally too if you want to test real email delivery during development.

---

## 4. Environment Variables

See `.env.example` for the full list with comments. Key ones:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DATABASE_URL` | Postgres connection string (empty = local SQLite) |
| `OVERDUE_THRESHOLD_DAYS` | Days before an open complaint is flagged overdue |
| `USE_CLOUDINARY` | `True` in production so photo/document uploads persist |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Cloudinary credentials |
| `BREVO_API_KEY` | Brevo API key (Settings → SMTP & API → **API Keys** tab, not the SMTP tab) — used to call Brevo's HTTP API directly |
| `DEFAULT_FROM_EMAIL` | The verified sender address emails are sent from |

> **Note:** email sending does **not** use Django's `EMAIL_BACKEND` / SMTP
> settings. `complaints/emails.py` calls Brevo's HTTP API
> (`https://api.brevo.com/v3/smtp/email`) directly via the `requests`
> library, authenticated with `BREVO_API_KEY`. This sidesteps SMTP ports
> (25/587) being blocked or unreliable on some free hosting tiers — the API
> call goes out over standard HTTPS instead. Make sure `requests` is listed
> in `requirements.txt`.

---

## 5. Deployment (as configured on the live instance)

1. **Database — [Neon](https://neon.tech):** create a free Postgres project,
   copy the connection string into `DATABASE_URL`.
2. **Photo/file storage — [Cloudinary](https://cloudinary.com):** create a
   free account, copy the Cloud Name / API Key / API Secret from the
   dashboard, set `USE_CLOUDINARY=True`.
3. **Email — [Brevo](https://www.brevo.com):** create a free account,
   verify a single sender email (no custom domain required). Then go to
   *Settings → SMTP & API → **API Keys*** tab (not the SMTP tab) and
   generate an API key — copy it into `BREVO_API_KEY`. Brevo's free tier
   (300 emails/day, no expiry) is the reason it's used here instead of
   SendGrid (60-day trial) or Resend (can't email arbitrary recipients
   without a verified domain). The app calls Brevo's HTTP API directly
   rather than going through SMTP, since free-tier hosts sometimes block or
   throttle outbound SMTP ports.
4. **Hosting — [Render](https://render.com):**
   - New → Web Service → connect the GitHub repo, branch `main`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn society_tracker.wsgi:application`
   - Add all the environment variables above (`DEBUG=False` in production)
   - Render auto-injects `RENDER_EXTERNAL_HOSTNAME`, which `settings.py`
     picks up into `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` automatically
5. **Create the first admin** — the free Render tier doesn't include Shell
   access, so run this from a local machine with `DATABASE_URL` pointed at
   the Neon connection string for that one command:
   ```bash
   $env:DATABASE_URL="<neon-connection-string>"   # PowerShell
   python manage.py createsuperuser
   python manage.py shell -c "
   from accounts.models import User
   u = User.objects.get(username='<username>')
   u.is_committee = True
   u.save()
   "
   ```

---

## 6. Database Schema

```
User (extends Django's AbstractUser)
├── id                 PK
├── username, email, password, first_name, last_name  (from AbstractUser)
├── wing               e.g. "A"
├── flat_number        e.g. "101"          — (wing, flat_number) is unique
├── phone_number
└── is_committee       boolean — additive permission, not an exclusive role

Complaint
├── id                 PK
├── resident           FK -> User
├── category           enum: plumbing | electrical | cleaning | security | lift | parking | other
├── description        text
├── photo              image (optional, uploaded by resident)
├── resolution_photo   image (optional, "after" photo attached by committee on resolve)
├── priority           enum: low | medium | high
├── status             enum: open | in_progress | resolved
├── created_at / updated_at / resolved_at
└── is_overdue         [computed property — status != resolved AND age > OVERDUE_THRESHOLD_DAYS]

StatusLog                              — the complaint's audit trail
├── id                 PK
├── complaint          FK -> Complaint
├── status             enum (snapshot at this point in time)
├── note               text (optional)
├── actor              FK -> User
└── timestamp

Notice
├── id                 PK
├── title, body
├── is_important       boolean — pins to top + triggers targeted email
├── author             FK -> User
├── target_type        enum: all | wing | resident
├── target_wing        e.g. "A"           — used when target_type = wing
├── target_resident     FK -> User (nullable) — used when target_type = resident
└── created_at

Rule
├── id, order, title, description, created_at

Contact
├── id, category (committee | emergency), name, designation, phone_number, notes

Document                                — committee-only file archive
├── id, title, description, file, uploaded_by (FK -> User), uploaded_at
```

**Relationships:** one `User` (resident) has many `Complaint`s; one
`Complaint` has many `StatusLog` entries (its history); one `User`
(committee) authors many `Notice`s / `Document`s.

---

## 7. Route Reference

Server-rendered app (no JSON API) — routes below are the Django views each
URL maps to.

### Auth (`/accounts/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET/POST | `/accounts/signup/` | Resident self-registration (wing + flat required) | Public |
| GET/POST | `/accounts/login/` | Login | Public |
| POST | `/accounts/logout/` | Logout | Authenticated |
| GET | `/accounts/directory/` | Searchable resident directory | Committee |
| GET | `/accounts/directory/export/` | CSV export of all residents | Committee |

### Complaints (`/complaints/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/complaints/redirect/` | Post-login landing redirect | Authenticated |
| GET/POST | `/complaints/raise/` | Raise a new complaint | Authenticated (any resident, incl. committee) |
| GET | `/complaints/mine/` | List the logged-in user's own complaints | Authenticated |
| GET | `/complaints/<id>/` | Complaint detail + full status history | Owner or Committee |
| GET | `/complaints/admin/` | All complaints — filter, search, paginate, overdue-first | Committee |
| GET/POST | `/complaints/admin/<id>/update/` | Update status/priority, attach resolution photo, sends email on status change | Committee |

### Notices (`/notices/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/notices/` | Notice board, filtered to notices addressed to the viewer | Authenticated |
| GET/POST | `/notices/post/` | Post a notice (all / wing / specific resident) | Committee |

### Community (`/community/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/community/rules/` | Rules & Regulations | Authenticated |
| GET/POST | `/community/rules/add/`, `/community/rules/<id>/edit/`, `/community/rules/<id>/delete/` | Manage rules | Committee |
| GET | `/community/contacts/` | Committee & emergency contacts | Authenticated |
| GET/POST | `/community/contacts/add/`, `/community/contacts/<id>/edit/`, `/community/contacts/<id>/delete/` | Manage contacts | Committee |

### Documents (`/documents/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/documents/` | Document archive | Committee |
| GET/POST | `/documents/upload/` | Upload a reference document | Committee |
| POST | `/documents/<id>/delete/` | Delete a document | Committee |

### Dashboard (`/dashboard/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/dashboard/` | Totals by status/category (charts) + overdue count | Committee |

### Django Admin
| Method | Path | Description |
|---|---|---|
| GET | `/admin-panel/` | Full Django admin — user management, raw data access |

---

## 8. Project Structure

```
society_tracker/
├── accounts/            # Custom User model, signup/login, resident directory
├── complaints/           # Complaint + StatusLog models, resident & admin views, email helper
├── notices/               # Notice board model + targeted views
├── community/              # Rules & Contacts (committee/emergency)
├── documents/                # Committee-only file archive
├── dashboard/                  # Admin dashboard aggregation + chart data
├── templates/                    # All HTML templates (Bootstrap 5 + custom design system)
├── static/                         # CSS, background image
├── society_tracker/                 # settings.py, urls.py, wsgi.py
├── requirements.txt
├── .env.example
├── build.sh                            # Render build script
├── Procfile                              # Render start command
└── manage.py
```

---

## 9. Key Design Decisions

- **Committee is additive, not exclusive** — every account is fundamentally a
  resident (wing + flat); `is_committee` just grants extra tools on top, so a
  committee member can also raise complaints for their own flat.
- **Wing + flat number, not name, is the unique identifier** — this is what
  disambiguates two residents who happen to share a name, and is enforced as
  a DB constraint at signup.
- **Complaint history is append-only** — `StatusLog` rows are never edited or
  deleted, so the full audit trail is always reconstructable.
- **Overdue status is computed, not stored** — a pure function of
  `created_at`, `status`, and a configurable threshold, so changing the
  threshold takes effect instantly with no migration or background job.
- **Notice targeting** — a notice can go to everyone, one wing, or one
  resident; both visibility on the board and the "important" email respect
  the same targeting.
- **Email via HTTP API, not SMTP** — `complaints/emails.py` posts directly
  to Brevo's REST endpoint using `requests`, rather than routing through
  Django's `EMAIL_BACKEND`/SMTP machinery. This was a deliberate switch
  during deployment: some free hosting tiers block or throttle outbound SMTP
  ports (25/587), while a plain HTTPS POST has no such restriction. The
  trade-off is that Django's built-in email backend abstraction is bypassed,
  so switching providers later means changing `_send_email()` directly
  rather than swapping a settings value — acceptable here for one integration.

See `SYSTEM_DESIGN.md` for the original write-up on the complaint history
model, overdue detection, photo handling, and notification flow.
