# Data Sources

The project is designed around official developer documentation instead of personal
notes or scraped Q&A content.

## Source manifest

Each entry in `sources.yaml` includes:

- `name`: stable source identifier used in metadata
- `type`: source loader type
- `repo` and `branch`: GitHub repository location when applicable
- `include`: file patterns to index
- `license`: license label shown in citations
- `attribution`: attribution text shown in metadata
- `homepage`: public documentation URL

## Why official docs?

Official docs are a practical fit for RAG because they are structured, versionable, and
source-grounded. The system can show which documentation page and section supported the
answer.
