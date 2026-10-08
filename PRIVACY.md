# Privacy and data handling

Personal Finance Tracker is designed to minimize exposure of financial data.

- Original CSV uploads are parsed in memory and are not written to disk.
- Only normalized transaction fields are persisted.
- Transactions, categories, and rules are scoped to the authenticated user.
- Passwords are stored as `scrypt` hashes, never as plaintext.
- Authentication tokens expire after 12 hours.
- The default local database is SQLite; production deployments should use encrypted storage and HTTPS.
- Do not use real bank statements in development or demos. Use anonymized data.

Before deploying publicly, configure a strong `JWT_SECRET`, use a managed encrypted database, restrict CORS to the deployed frontend origin, and add a data deletion workflow.
