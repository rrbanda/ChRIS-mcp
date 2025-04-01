# US-01: List Available Plugins from ChRIS

## User Story

As a user,  
I want to retrieve a list of available plugins from ChRIS,  
So that I can choose which one to run.

## Endpoint

`GET /api/v1/plugins/`

## MCP Function

`list_plugins`

## Input

- `username`: ChRIS username
- `password`: ChRIS password

## Output

A list of plugin names and IDs, for example:

```json
[
  {"id": 1, "name": "pl-dircopy"},
  {"id": 2, "name": "pl-simpledsapp"}
]
```

## Notes

- Authentication is required
- Uses the Collection+JSON format
