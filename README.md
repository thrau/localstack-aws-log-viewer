LocalStack AWS Log Viewer
=========================

[![Install LocalStack Extension](https://localstack.cloud/gh/extension-badge.svg)](https://app.localstack.cloud/extensions/remote?url=git+https://github.com/thrau/localstack-aws-log-viewer/#egg=localstack-aws-log-viewer)

The LocalStack AWS Log Viewer extension allows you to view and inspect your LocalStack AWS request logs directly from the browser.

## Get started

### Install

Start LocalStack and click the LocalStack Extension badge on the top of the README.

Alternatively, you can install the extension via the CLI directly from this repository:

```bash
localstack extensions install "git+https://github.com/thrau/localstack-aws-log-viewer/#egg=localstack-aws-log-viewer"
```

### Use the webapp

Navigate to http://aws-log-viewer.localhost.localstack.cloud:4566.
As you make AWS requests to LocalStack, they will appear in the log viewer.
Click on individual requests to see details about the request and response payloads.

## Develop

To install the extension into localstack in developer mode, you will need Python 3.10, and create a virtual environment in the extensions project.

In the newly generated project, simply run

```bash
make install
```

Then, to enable the extension for LocalStack, run

```bash
localstack extensions dev enable .
```

You can then start LocalStack with `EXTENSION_DEV_MODE=1` to load all enabled extensions:

```bash
EXTENSION_DEV_MODE=1 localstack start
```
