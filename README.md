# Booking System

A web-based booking system developed with Python and Django.

## About the Project

This project is a Django-based booking system designed to manage users, services and bookings through a simple web interface.

The project was created as a practical learning project to develop Python, Django, database, Git and software testing skills.

## Features

* User registration and authentication
* Service management
* Booking management
* User accounts
* Admin functionality
* Database integration
* Responsive web interface

## Technologies

* Python
* Django
* SQLite
* HTML
* CSS
* Git
* GitHub

## Project Status

**In development**

New features and improvements are being added as part of ongoing learning and development.

## Author

**Viola M.**

GitHub: [@vlmslnk](https://github.com/vlmslnk)

## API Contract

### Authentication

Booking endpoints require JWT authentication.

Send the access token in the request header:

`Authorization: Bearer <access_token>`

### Create a booking

**Endpoint:** `POST /api/bookings/`

**Content-Type:** `application/json`

Example request:

```json
{
  "service": 1,
  "specialist": 1,
  "customer_name": "Test Client",
  "customer_phone": "123456789",
  "date": "2026-10-19",
  "time": "09:00"
}

cat >> README.md <<'EOF'

## API Contract

### Authentication

Booking endpoints require JWT authentication.

Header:
`Authorization: Bearer <access_token>`

### Create a booking

**Endpoint:** `POST /api/bookings/`

**Content-Type:** `application/json`

Example request:

```json
{
  "service": 1,
  "specialist": 1,
  "customer_name": "Test Client",
  "customer_phone": "123456789",
  "date": "2026-10-19",
  "time": "09:00"
}
```

### Date and time format

- `date`: `YYYY-MM-DD`, for example `2026-10-19`.
- `time`: `HH:MM` in 24-hour format, for example `09:00`.
- Booking dates and times are interpreted in UTC.
- `created_at` uses ISO 8601 format with timezone information.

### Responses

- **201 Created** — booking successfully created.
- **400 Bad Request** — invalid input or unavailable time that is not an existing booking conflict.
- **409 Conflict** — the requested time overlaps an existing scheduled booking.

Example conflict response:

```json
{
  "code": "slot_unavailable",
  "detail": "Это время уже занято. Выберите другой слот."
}
```
