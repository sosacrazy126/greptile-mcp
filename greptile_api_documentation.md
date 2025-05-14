# Greptile API Documentation

## Introduction

Greptile is a powerful code search and understanding tool that allows you to index and query repositories using natural language. This documentation provides a comprehensive guide to using the Greptile API.

## Base URL

All API requests should be made to the following base URL:

```
https://api.greptile.com/v2/
```

## Authentication

Two tokens are required for authentication:

1. **Greptile API Key**:
   - Include in the request header: `Authorization: Bearer <API_KEY>`
   - Get your API key from [Greptile App](https://app.greptile.com/login)

2. **GitHub/GitLab Token**:
   - Include in the request header: `X-GitHub-Token: <GITHUB_TOKEN>`
   - The read permissions on this token determine which repositories Greptile can access

## API Endpoints

### 1. Index Repository

Initiates processing or reprocessing of a specified repository.

**Endpoint**: `POST /repositories`

**Headers**:
- `Authorization: Bearer <API_KEY>`
- `Content-Type: application/json`
- `X-GitHub-Token: <GITHUB_TOKEN>`

**Request Body**:
```json
{
  "remote": "<string>",       // "github" or "gitlab"
  "repository": "<string>",   // Format: "owner/repository"
  "branch": "<string>",       // Branch name to index
  "reload": true,             // Optional, default true. If false, won't reprocess if previously successful
  "notify": true              // Optional, default true. Whether to notify the user upon completion
}
```

**Response**:
```json
{
  "message": "<string>",      // Processing status message
  "statusEndpoint": "<string>" // URL to check the status of the repository processing
}
```

### 2. Query Repository

Submit a natural language query about the codebase to get a natural language answer with a list of relevant code references.

**Endpoint**: `POST /query`

**Headers**:
- `Authorization: Bearer <API_KEY>`
- `Content-Type: application/json`
- `X-GitHub-Token: <GITHUB_TOKEN>`

**Request Body**:
```json
{
  "messages": [
    {
      "id": "<string>",
      "content": "<string>",  // Your natural language query
      "role": "<string>"
    }
  ],
  "repositories": [
    {
      "remote": "<string>",   // "github" or "gitlab"
      "branch": "<string>",   // Branch name
      "repository": "<string>" // Format: "owner/repository"
    }
  ],
  "sessionId": "<string>",    // Optional, defaults to a new session
  "stream": true,             // Optional, default false
  "genius": true              // Optional, default false. Genius requests are smarter but slower
}
```

**Response**:
```json
{
  "message": "<string>",      // The answer to your query
  "sources": [
    {
      "repository": "<string>", // Repository name
      "remote": "<string>",     // Remote service (github/gitlab)
      "branch": "<string>",     // Branch name
      "filepath": "<string>",   // Relative path to the file
      "linestart": 123,         // Starting line number
      "lineend": 123,           // Ending line number
      "summary": "<string>"     // Summary of the file contents
    }
  ]
}
```

### 3. Search Repository

Similar to Query, but only returns the list of relevant files without generating an answer.

**Endpoint**: `POST /search`

**Headers**:
- `Authorization: Bearer <API_KEY>`
- `Content-Type: application/json`
- `X-GitHub-Token: <GITHUB_TOKEN>`

**Request Body**: Same as Query endpoint

**Response**: Same format as Query endpoint but without the answer

### 4. Get Repository Info

Retrieves information about a specific repository.

**Endpoint**: `GET /repositories/{repositoryId}`

**Path Parameters**:
- `repositoryId`: URL-encoded in the format `remote:branch:owner/repository`

**Headers**:
- `Authorization: Bearer <API_KEY>`

**Response**:
```json
{
  "repository": "<string>",   // Repository name
  "remote": "<string>",       // Remote service (github/gitlab)
  "branch": "<string>",       // Branch name
  "private": true,            // Whether the repository is private
  "status": "<string>",       // Processing status
  "filesProcessed": 123,      // Number of files processed
  "numFiles": 123,            // Total number of files
  "sha": "<string>"           // Commit SHA
}
```

## Example Usage

### Indexing a Repository

```bash
curl --request POST \
  --url https://api.greptile.com/v2/repositories \
  --header 'Authorization: Bearer <YOUR_API_KEY>' \
  --header 'Content-Type: application/json' \
  --header 'X-GitHub-Token: <YOUR_GITHUB_TOKEN>' \
  --data '{
  "remote": "github",
  "repository": "username/repo-name",
  "branch": "main",
  "reload": true,
  "notify": true
}'
```

### Querying a Repository

```bash
curl --request POST \
  --url https://api.greptile.com/v2/query \
  --header 'Authorization: Bearer <YOUR_API_KEY>' \
  --header 'Content-Type: application/json' \
  --header 'X-GitHub-Token: <YOUR_GITHUB_TOKEN>' \
  --data '{
  "messages": [
    {
      "id": "query1",
      "content": "How does authentication work in this codebase?",
      "role": "user"
    }
  ],
  "repositories": [
    {
      "remote": "github",
      "branch": "main",
      "repository": "username/repo-name"
    }
  ],
  "genius": true
}'
```

### Getting Repository Information

```bash
curl --request GET \
  --url https://api.greptile.com/v2/repositories/github:main:username%2Frepo-name \
  --header 'Authorization: Bearer <YOUR_API_KEY>'
```

## Order of Operations

1. **Index Repository**: Submit a repository to be indexed
2. **Query Repository**: Query the indexed repository with natural language
3. **Optional - Search Repository**: Search for relevant files without generating an answer

## Notes

- Before Greptile can query a repository, it must be indexed first.
- Genius requests are smarter but 8-10 seconds slower, great for complex use cases.
- The read permissions on the GitHub/GitLab token determine which repositories Greptile can access.
