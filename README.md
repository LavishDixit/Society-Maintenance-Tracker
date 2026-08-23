# Society Maintenance Tracker

A web platform for apartment societies to manage maintenance complaints end to end:
residents raise complaints with photos, admins triage and resolve them through a
tracked workflow, and everyone stays informed via a notice board and email alerts.

Built with **Django** (server-rendered templates + Bootstrap 5), **PostgreSQL**,
**Cloudinary** for photo storage, and **SendGrid** for email.

---

## 1. Features

**Resident**
- Register and log in
- Raise a complaint with category, description, and an optional photo
- View all of their own complaints with the full status history of each

**Admin**
- View all complaints; filter by category, status, and date range
- Set complaint priority (Low / Medium / High)
- Update complaint status (Open → In Progress → Resolved), each change is
  recorded with a timestamp, actor, and optional note
- Complaints open longer than a configurable threshold are flagged **Overdue**
  and surfaced at the top of the list
- Post notices to a society-wide notice board; mark a notice **Important** to
  pin it to the top and trigger an email blast to all residents
- Dashboard: total complaints, breakdown by status, breakdown by category,
  and a live overdue count

**System-wide**
- Role-based authentication (resident / admin) — admins are created via the
  Django admin panel or `createsuperuser`, not through public sign-up
- Every status change is appended to an immutable history log — nothing is
  ever overwritten
- Emails sent automatically on status change and on important notices

---

## 2. Tech Stack

| Layer          | Choice                                             |
|----------------|-----------------------------------------------------|
| Backend        | Django 6.1                                          |
| Frontend       | Django Templates + Bootstrap 5 (server-rendered)    |
| Database       | PostgreSQL (SQLite for local dev)                   |
| Photo storage  | Cloudinary (free tier)                              |
| Email          | SendGrid (free tier, via SMTP relay)                |
| Hosting        | Render (or Railway/any host that runs Django + Postgres) |
| Static files   | WhiteNoise                                          |

---

## 3. Local Setup

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# 1. Clone the repo and enter it
git clone <your-repo-url>
cd society-maintenance-tracker

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file and fill in values
cp .env.example .env
# By default DEBUG=True and DATABASE_URL is empty, which means the app
# runs on local SQLite out of the box - no Postgres/Cloudinary/SendGrid
# setup required just to try it locally.

# 5. Run migrations
python manage.py migrate

# 6. Create an admin account
python manage.py createsuperuser
# then open the Django admin at /admin-panel/ and set that user's
# "role" field to Admin (or do it via the shell, see below)

python manage.py shell -c "
from accounts.models import User
u = User.objects.get(username='<your-username>')
u.role = User.Role.ADMIN
u.save()
"

# 7. Run the dev server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — it redirects to the login page.
- Log in with your admin account to see the admin dashboard, complaint list, and notice posting.
- Sign up as a new user via "Sign Up" to try the resident flow (raise complaint, view history).

In local dev, emails are printed to the console instead of actually sent
(`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` by default).

---

## 4. Environment Variables

All configuration lives in `.env` (see `.env.example` for the full list with
comments). Key ones:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DATABASE_URL` | Postgres connection string (empty = local SQLite) |
| `OVERDUE_THRESHOLD_DAYS` | Days before an open complaint is flagged overdue |
| `USE_CLOUDINARY` | `True` in production so photo uploads persist |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Cloudinary credentials |
| `EMAIL_BACKEND` | Console backend locally, SMTP backend in production |
| `SENDGRID_API_KEY` | SendGrid API key (used as the SMTP password) |
| `DEFAULT_FROM_EMAIL` | The "from" address on outgoing emails |

---

## 5. Deploying to Render

1. Push the repo to GitHub (branch `main`, public).
2. Create a new **PostgreSQL** instance on Render (free tier) — copy its
   internal connection string.
3. Create a new **Web Service** on Render, pointing at your repo:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn society_tracker.wsgi:application`
4. Set environment variables on the Render dashboard (mirror `.env.example`):
   - `DATABASE_URL` = the Postgres connection string from step 2
   - `DEBUG=False`
   - `USE_CLOUDINARY=True` + your Cloudinary credentials
   - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` + your `SENDGRID_API_KEY`
   - `SECRET_KEY` = a freshly generated secret
5. Deploy. Render automatically injects `RENDER_EXTERNAL_HOSTNAME`, which
   `settings.py` picks up and adds to `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`
   automatically — no manual config needed there.
6. Once live, create your admin user with:
   `python manage.py createsuperuser` via Render's shell tab, then set their
   role to Admin the same way as in local setup.

(Railway works the same way — Postgres add-on + a service pointed at this
repo with the same build/start commands and env vars.)

---

## 6. Database Schema

```
User (extends Django's AbstractUser)
├── id                PK
├── username, email, password    (from AbstractUser)
├── role               enum: resident | admin
├── flat_number        e.g. "A-101"
└── phone_number

Complaint
├── id                 PK
├── resident           FK -> User
├── category           enum: plumbing | electrical | cleaning | security | lift | parking | other
├── description        text
├── photo              image (optional)
├── priority           enum: low | medium | high
├── status             enum: open | in_progress | resolved
├── created_at
├── updated_at
├── resolved_at        (set automatically when status -> resolved)
└── is_overdue         [computed property, not a column - see section 7]

StatusLog                              -- the complaint history / audit trail
├── id                 PK
├── complaint          FK -> Complaint
├── status             enum (snapshot of status at this point in time)
├── note               text (optional, e.g. "Plumber assigned")
├── actor              FK -> User (who made this change)
└── timestamp

Notice
├── id                 PK
├── title
├── body
├── is_important       boolean (pins to top of notice board + triggers email)
├── author             FK -> User
└── created_at
```

Relationships: one `User` (resident) has many `Complaint`s; one `Complaint`
has many `StatusLog` entries (its history); one `User` (admin) authors many
`Notice`s.

---

## 7. API / Endpoint Reference

This app is server-rendered (no JSON API), so "endpoints" below are the
Django URL routes each view handles.

### Auth (`/accounts/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET/POST | `/accounts/signup/` | Resident self-registration | Public |
| GET/POST | `/accounts/login/` | Login | Public |
| POST | `/accounts/logout/` | Logout | Authenticated |

### Complaints (`/complaints/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/complaints/redirect/` | Post-login redirect to the right home screen | Authenticated |
| GET/POST | `/complaints/raise/` | Raise a new complaint (category, description, photo) | Resident |
| GET | `/complaints/mine/` | List the logged-in resident's own complaints | Resident |
| GET | `/complaints/<id>/` | Complaint detail + full status history | Owner resident or Admin |
| GET | `/complaints/admin/` | All complaints, filterable by `?category=&status=&date_from=&date_to=`, overdue pinned to top | Admin |
| GET/POST | `/complaints/admin/<id>/update/` | Update status/priority (writes a `StatusLog` entry, sends email on status change) | Admin |

### Notices (`/notices/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/notices/` | Notice board (important notices pinned to top) | Authenticated |
| GET/POST | `/notices/post/` | Post a new notice, optionally marked Important | Admin |

### Dashboard (`/dashboard/`)
| Method | Path | Description | Access |
|---|---|---|---|
| GET | `/dashboard/` | Totals by status, by category, and overdue count | Admin |

### Django Admin
| Method | Path | Description |
|---|---|---|
| GET | `/admin-panel/` | Full Django admin (user management, raw data access) |

---

## 8. Project Structure

```
society_tracker/
├── accounts/          # Custom User model, signup/login/logout
├── complaints/        # Complaint + StatusLog models, resident & admin views, email helpers
├── notices/           # Notice board model + views
├── dashboard/          # Admin dashboard aggregation view
├── templates/          # All HTML templates (Bootstrap 5)
├── static/             # CSS
├── society_tracker/    # settings.py, urls.py, wsgi.py
├── requirements.txt
├── .env.example
├── build.sh            # Render build script
├── Procfile             # Render/Railway start command
└── manage.py
```

---

## 9. Notes on Design Decisions

See `SYSTEM_DESIGN.md` for the full write-up on the complaint history model,
overdue detection, photo handling, and notification flow.
