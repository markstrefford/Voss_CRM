# Changelog

## [Unreleased]

### Added
- Modal deployment for VOSS API endpoints (`backend/modal_app.py`)
- Rate limiting on auth endpoints (SlowAPI)
- Security hardening: HMAC-constant-time API key comparison, production secret validation, security headers
- Dockerfile for containerised deployment

### Changed
- VOSS API now deployable on Modal (was localhost only)
- Chrome extension: better error messages on failed API calls
- Chrome extension: page-title fallback for LinkedIn name scraping

### Removed
- Local Telegram polling disabled on Modal (replaced by NanoClaw North agent)
