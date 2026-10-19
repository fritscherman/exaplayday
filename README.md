# EXAPLAY Tech Day Guest Lab

Collaborative guest shortlist with SQLite, live refresh (10 seconds) and Basic Auth. Both pages follow the VIOSO corporate design (Quicksand, #0095db / #00eaa9 on #212121, diagonal gradients, oblique lines, hexagon pattern) via `static/vioso.css`.

`/` and `/api/*` require Basic Auth. `/event` (the invitation page linked from the e-mails) and `/static/*` are public so invited guests can open the agenda without a login.

## Deploy using Coolify

GitHub repository: `fritscherman/exaplayday`, branch `main`.

Choose Docker Compose deployment (`docker-compose.yml`), set environment variables `APP_USER=vioso` and `APP_PASSWORD` to the password supplied separately. Do not commit your password. Set up HTTPS in Coolify; HTTP Basic Auth should **only** be used over HTTPS. Expose the service using port 8080. Persistent named Docker volume `exaplay_guest_data` holds `/app/data/exaplay.sqlite3` and survives container restarts and redeployments.

Start/redeploy the application. First startup initializes a candidate list (without 3Made or Marcus Schäfer). Once initialized, subsequent deployments never overwrite team edits. Startup also applies `PROPOSED_CONTACTS` / `PROPOSED_LEADS` from `server.py`: publicly researched addresses fill **empty** e-mail fields only and add a `Vorschlag (…, Quelle: …), bitte prüfen` note, so the team verifies before inviting. Rows still named `Technischer Lead` are renamed to the researched contact.

## Guest workflow

Each guest has selection Ja/Nein/Offen, owner, invitation text, done checkbox, feedback, RSVP (Offen/Zusage/Absage/Vielleicht), hotel, food preference, +1 / colleague, country, email and notes. Click Bearbeiten on a guest to edit. Add new guests at bottom. Changes are stored in SQLite centrally, with refresh every 10 seconds. CSV export is available. Invite sending is manual: this app stores draft text and tracking, **it does not send emails**. Each row has an **E-Mail erstellen** button that opens the invitation dialog directly; the generated text is personal (first name, company, optional personal hook, sender name) and available in English (main) and German. The event page is bilingual too: EN/DE toggle, `?lang=de` for the German version.

All authenticated users share the same account and can edit every entry. For stronger audit trails and person-specific accounts, extend authentication and change logging in a later version. Back up the `exaplay_guest_data` volume routinely. Avoid storing sensitive dietary medical diagnoses; only necessary catering preferences.
