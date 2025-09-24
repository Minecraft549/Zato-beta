# Zato Pub/Sub Subscription API

## Overview

The Zato Pub/Sub REST API allows external clients to subscribe to topics to receive messages. This document explains how to subscribe to topics and manage your subscriptions.

## Authentication

All requests require HTTP Basic Authentication using your Zato security credentials.

## Subscribe to a Topic

Subscribe to receive messages from a specific topic.

### Endpoint
```
POST /topic/{topic_name}/subscribe
```

### Parameters
- `topic_name` - The name of the topic to subscribe to

### Topic Name Restrictions
Topic names must adhere to the following rules:
- Maximum length: 200 characters
- The "#" character is not allowed in topic names
- Only ASCII characters are permitted



### Request Body
No request body required.

### Response

#### Success (200 OK)
```json
{
  "is_ok": true,
  "cid": "correlation-id",
  "status": "200 OK"
}
```

#### Error (401 Unauthorized)
```json
{
  "is_ok": false,
  "cid": "correlation-id",
  "details": "Authentication failed",
  "status": "401 Unauthorized"
}
```

#### Error (400 Bad Request)
```json
{
  "is_ok": false,
  "cid": "correlation-id",
  "details": "Topic name validation error",
  "status": "400 Bad Request"
}
```

### Examples

#### Subscribe to Order Events
```bash
curl -X POST \
  -u username:password \
  http://localhost:44556/topic/orders.processed/subscribe
```

#### Subscribe to Wildcard Pattern Topic
```bash
curl -X POST \
  -u username:password \
  http://localhost:44556/topic/alerts.critical.system/subscribe
```

### Topic Auto-Creation
- Topics are automatically created when you subscribe to them if they don't exist
- No pre-configuration of topics is required

### More About Subscriptions
- Subscribing to the same topic multiple times is safe and has no effect
- The system recognizes existing subscriptions and returns success without changes when you subscribe to the same topic twice or more
- Subscriptions remain active until explicitly unsubscribed

### Message Queues
- Each user gets a unique subscription key that identifies their own message queue
- Messages from all subscribed topics are delivered to that one queue
- Use the `/messages/get` endpoint to retrieve messages
- Delivery type is set to 'Pull' for REST API subscriptions

## Topic Permissions

Your user account must have subscription permissions for the topics you want to subscribe to. Permissions are configured using pattern matching.

### Permission Examples
```
sub=orders.*           # Can subscribe to orders.processed, orders.cancelled, etc.
sub=alerts.**          # Can subscribe to any alerts topic at any depth
sub=notifications.user.email  # Can only subscribe to this exact topic
```

## Error Handling

Common error scenarios:

### Authentication Errors
- **401 Unauthorized** - Invalid credentials provided in HTTP Basic Auth

### Topic Validation Errors
- **400 Bad Request** - Topic name violates restrictions (length, characters, etc.)

### Server Errors
- **400 Bad Request** - Database error during subscription creation
- **500 Internal Server Error** - Unexpected server-side error

## Technical Implementation

### Subscription Keys
- Each user receives a unique subscription key (sub_key)
- The same sub_key is used no matter to how many topics you subscribe

## Next Steps

After subscribing to topics:

1. **Retrieve Messages** - Use `POST /messages/get` to pull messages
2. **Unsubscribe** - Use `POST /topic/{topic_name}/unsubscribe` when done
3. **Publish Messages** - Use `POST /topic/{topic_name}/publish` to send messages
