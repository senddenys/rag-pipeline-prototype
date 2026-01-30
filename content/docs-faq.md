# FAQ

## How do I reset my password?

Go to the account page at https://app.company.com/account and click "Reset password". You will receive an email with a link. The link expires in 24 hours.

## Can I use the API from a script?

Yes. Use the same Bearer token you get from `platform auth token`. We recommend storing it in an environment variable (e.g. `PLATFORM_TOKEN`) and not committing it to version control.

## What file formats are supported for datasets?

We support CSV, Parquet, and JSON Lines. For CSV, the first row must be headers. Max file size per upload is 500 MB. For larger data, use chunked upload or a sync connector.

## How long are pipeline runs kept?

Run history is kept for 90 days. After that, logs and artifacts are deleted. Export results to your own storage if you need longer retention.

## Who do I contact for support?

Email support@company.com or open a ticket in the internal #platform-support channel. For API bugs, include the request ID from the `X-Request-Id` response header.
