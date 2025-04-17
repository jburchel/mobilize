# Mobilize CRM API Documentation

This document provides comprehensive documentation for the Mobilize CRM API endpoints.

## Authentication

All API requests require authentication. The Mobilize CRM API uses JWT tokens for authentication.

### Getting an Authentication Token

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "role": "admin",
    "office_id": 1
  }
}
```

### Using Authentication Tokens

Include the token in the Authorization header of your requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refreshing a Token

**Endpoint:** `POST /api/auth/refresh`

**Headers:**
```
Authorization: Bearer your_refresh_token_here
```

**Response:**
```json
{
  "access_token": "new_access_token_here"
}
```

## User Management

### Get Current User

**Endpoint:** `GET /api/v1/users/me`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "User Name",
  "role": "admin",
  "office_id": 1,
  "permissions": ["read:contacts", "write:contacts", "manage:users"]
}
```

### List Users

**Endpoint:** `GET /api/v1/users`

**Query Parameters:**
- `office_id` (optional): Filter users by office ID
- `role` (optional): Filter users by role
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "User Name",
      "role": "admin",
      "office_id": 1
    },
    {
      "id": 2,
      "email": "user2@example.com",
      "name": "User 2",
      "role": "user",
      "office_id": 1
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

### Create User

**Endpoint:** `POST /api/v1/users`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "securepassword",
  "role": "user",
  "office_id": 1
}
```

**Response:**
```json
{
  "id": 3,
  "email": "newuser@example.com",
  "name": "New User",
  "role": "user",
  "office_id": 1
}
```

## Office Management

### List Offices

**Endpoint:** `GET /api/v1/offices`

**Response:**
```json
{
  "offices": [
    {
      "id": 1,
      "name": "Headquarters",
      "address": "123 Main St",
      "city": "Anytown",
      "state": "CA",
      "zip": "12345",
      "phone": "555-123-4567",
      "created_at": "2023-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Branch Office",
      "address": "456 Oak St",
      "city": "Somewhere",
      "state": "NY",
      "zip": "67890",
      "phone": "555-987-6543",
      "created_at": "2023-02-01T00:00:00Z"
    }
  ]
}
```

### Create Office

**Endpoint:** `POST /api/v1/offices`

**Request Body:**
```json
{
  "name": "New Office",
  "address": "789 Pine St",
  "city": "Elsewhere",
  "state": "TX",
  "zip": "45678",
  "phone": "555-555-5555"
}
```

**Response:**
```json
{
  "id": 3,
  "name": "New Office",
  "address": "789 Pine St",
  "city": "Elsewhere",
  "state": "TX",
  "zip": "45678",
  "phone": "555-555-5555",
  "created_at": "2023-03-01T00:00:00Z"
}
```

## Contact Management

### List Contacts

**Endpoint:** `GET /api/v1/contacts`

**Query Parameters:**
- `office_id` (optional): Filter contacts by office ID
- `search` (optional): Search term for name, email, or phone
- `status` (optional): Filter by status
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "contacts": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "555-123-4567",
      "status": "active",
      "office_id": 1,
      "created_at": "2023-01-15T00:00:00Z",
      "updated_at": "2023-01-15T00:00:00Z"
    },
    {
      "id": 2,
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "phone": "555-987-6543",
      "status": "active",
      "office_id": 1,
      "created_at": "2023-01-20T00:00:00Z",
      "updated_at": "2023-01-20T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

### Create Contact

**Endpoint:** `POST /api/v1/contacts`

**Request Body:**
```json
{
  "first_name": "Robert",
  "last_name": "Johnson",
  "email": "robert.johnson@example.com",
  "phone": "555-111-2222",
  "status": "active",
  "office_id": 1,
  "address": {
    "street": "123 Elm St",
    "city": "Somewhere",
    "state": "CA",
    "zip": "12345"
  }
}
```

**Response:**
```json
{
  "id": 3,
  "first_name": "Robert",
  "last_name": "Johnson",
  "email": "robert.johnson@example.com",
  "phone": "555-111-2222",
  "status": "active",
  "office_id": 1,
  "address": {
    "street": "123 Elm St",
    "city": "Somewhere",
    "state": "CA",
    "zip": "12345"
  },
  "created_at": "2023-03-10T00:00:00Z",
  "updated_at": "2023-03-10T00:00:00Z"
}
```

## Pipeline Management

### List Pipelines

**Endpoint:** `GET /api/v1/pipelines`

**Response:**
```json
{
  "pipelines": [
    {
      "id": 1,
      "name": "Person Pipeline",
      "description": "Main pipeline for person contacts",
      "office_id": 1,
      "stages": [
        {
          "id": 1,
          "name": "Lead",
          "order": 1
        },
        {
          "id": 2,
          "name": "Qualified",
          "order": 2
        },
        {
          "id": 3,
          "name": "Converted",
          "order": 3
        }
      ]
    },
    {
      "id": 2,
      "name": "Church Pipeline",
      "description": "Pipeline for church contacts",
      "office_id": 1,
      "stages": [
        {
          "id": 4,
          "name": "Initial Contact",
          "order": 1
        },
        {
          "id": 5,
          "name": "Meeting Scheduled",
          "order": 2
        },
        {
          "id": 6,
          "name": "Partnership",
          "order": 3
        }
      ]
    }
  ]
}
```

### Get Pipeline Details

**Endpoint:** `GET /api/v1/pipelines/{pipeline_id}`

**Response:**
```json
{
  "id": 1,
  "name": "Person Pipeline",
  "description": "Main pipeline for person contacts",
  "office_id": 1,
  "stages": [
    {
      "id": 1,
      "name": "Lead",
      "order": 1,
      "contacts_count": 10
    },
    {
      "id": 2,
      "name": "Qualified",
      "order": 2,
      "contacts_count": 5
    },
    {
      "id": 3,
      "name": "Converted",
      "order": 3,
      "contacts_count": 2
    }
  ],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Add Contact to Pipeline Stage

**Endpoint:** `POST /api/v1/pipelines/{pipeline_id}/stages/{stage_id}/contacts`

**Request Body:**
```json
{
  "contact_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Contact added to pipeline stage",
  "pipeline_contact": {
    "id": 1,
    "pipeline_id": 1,
    "stage_id": 1,
    "contact_id": 1,
    "created_at": "2023-03-15T00:00:00Z"
  }
}
```

## Task Management

### List Tasks

**Endpoint:** `GET /api/v1/tasks`

**Query Parameters:**
- `office_id` (optional): Filter tasks by office ID
- `user_id` (optional): Filter tasks by assigned user ID
- `contact_id` (optional): Filter tasks by related contact ID
- `status` (optional): Filter by status (open, completed)
- `due_date` (optional): Filter by due date
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Follow up with John",
      "description": "Call to discuss partnership opportunity",
      "status": "open",
      "due_date": "2023-04-01T00:00:00Z",
      "user_id": 1,
      "contact_id": 1,
      "office_id": 1,
      "created_at": "2023-03-20T00:00:00Z",
      "updated_at": "2023-03-20T00:00:00Z"
    },
    {
      "id": 2,
      "title": "Send proposal to Jane",
      "description": "Email the partnership proposal",
      "status": "open",
      "due_date": "2023-04-05T00:00:00Z",
      "user_id": 1,
      "contact_id": 2,
      "office_id": 1,
      "created_at": "2023-03-22T00:00:00Z",
      "updated_at": "2023-03-22T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

### Create Task

**Endpoint:** `POST /api/v1/tasks`

**Request Body:**
```json
{
  "title": "Schedule meeting with Robert",
  "description": "Discuss project collaboration",
  "due_date": "2023-04-10T14:00:00Z",
  "user_id": 1,
  "contact_id": 3,
  "office_id": 1
}
```

**Response:**
```json
{
  "id": 3,
  "title": "Schedule meeting with Robert",
  "description": "Discuss project collaboration",
  "status": "open",
  "due_date": "2023-04-10T14:00:00Z",
  "user_id": 1,
  "contact_id": 3,
  "office_id": 1,
  "created_at": "2023-03-25T00:00:00Z",
  "updated_at": "2023-03-25T00:00:00Z"
}
```

## Communication Management

### List Communications

**Endpoint:** `GET /api/v1/communications`

**Query Parameters:**
- `office_id` (optional): Filter by office ID
- `contact_id` (optional): Filter by contact ID
- `type` (optional): Filter by type (email, call, meeting)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "communications": [
    {
      "id": 1,
      "type": "email",
      "subject": "Introduction",
      "body": "Hello, I'm reaching out to introduce our organization...",
      "contact_id": 1,
      "user_id": 1,
      "office_id": 1,
      "sent_at": "2023-03-01T10:30:00Z",
      "created_at": "2023-03-01T10:30:00Z"
    },
    {
      "id": 2,
      "type": "call",
      "subject": "Follow-up call",
      "body": "Discussed partnership opportunities. Contact interested in learning more.",
      "contact_id": 2,
      "user_id": 1,
      "office_id": 1,
      "sent_at": "2023-03-05T14:15:00Z",
      "created_at": "2023-03-05T14:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

### Create Communication

**Endpoint:** `POST /api/v1/communications`

**Request Body:**
```json
{
  "type": "email",
  "subject": "Project Proposal",
  "body": "Dear Robert, Please find attached our project proposal...",
  "contact_id": 3,
  "user_id": 1,
  "office_id": 1,
  "sent_at": "2023-03-26T09:45:00Z"
}
```

**Response:**
```json
{
  "id": 3,
  "type": "email",
  "subject": "Project Proposal",
  "body": "Dear Robert, Please find attached our project proposal...",
  "contact_id": 3,
  "user_id": 1,
  "office_id": 1,
  "sent_at": "2023-03-26T09:45:00Z",
  "created_at": "2023-03-26T09:45:00Z"
}
```

## Google Integration

### Sync Google Contacts

**Endpoint:** `POST /api/v1/google/sync/contacts`

**Response:**
```json
{
  "success": true,
  "message": "Google contacts sync initiated",
  "job_id": "sync-job-123"
}
```

### Get Sync Status

**Endpoint:** `GET /api/v1/google/sync/status/{job_id}`

**Response:**
```json
{
  "job_id": "sync-job-123",
  "status": "completed",
  "started_at": "2023-03-27T10:00:00Z",
  "completed_at": "2023-03-27T10:05:00Z",
  "items_processed": 50,
  "items_created": 10,
  "items_updated": 5,
  "items_failed": 0
}
```

### List Google Contacts

**Endpoint:** `GET /api/v1/google/contacts`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:**
```json
{
  "contacts": [
    {
      "id": "google-contact-id-1",
      "name": "John Smith",
      "email": "john.smith@example.com",
      "phone": "555-123-4567",
      "imported": true,
      "crm_contact_id": 1
    },
    {
      "id": "google-contact-id-2",
      "name": "Jane Doe",
      "email": "jane.doe@example.com",
      "phone": "555-987-6543",
      "imported": false,
      "crm_contact_id": null
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common error codes:
- `unauthorized`: Authentication is required
- `forbidden`: Insufficient permissions
- `not_found`: Resource not found
- `validation_error`: Invalid input data
- `server_error`: Internal server error

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 200 requests per hour per IP address
- 1000 requests per hour per authenticated user

When a rate limit is exceeded, the API returns a 429 Too Many Requests response with a Retry-After header.

## Versioning

The API is versioned using URL path versioning (e.g., `/api/v1/`). The current version is v1.

When breaking changes are introduced, a new version will be released (e.g., `/api/v2/`). 