# Changelog

All notable changes to the Griptape Nodes Topaz Labs Library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/), and each version is
the `library_version` in `topazlabs/griptape_nodes_library.json`.
**Breaking** marks a change that can stop a saved workflow from working without edits.

## [Unreleased]

<!-- Entries go in changelog.d/, one file each. See changelog.d/README.md. -->

## [0.2.0] - 2026-11-06

### Changed

- **Breaking:** a missing `TOPAZ_LABS_API_KEY` is reported when the node runs, on the node, with a
  link to the key in Settings, and no longer when the flow starts. Nodes upstream of a Topaz Labs
  node run first. The key is reported on its own, before any other problem. Out-of-range values on
  the denoise, enhance and video nodes are also reported when the node runs, not at flow start.
  [#14](https://github.com/griptape-ai/griptape-nodes-library-topazlabs/issues/14)
- The library requires Griptape Nodes engine 0.105.0 or later.
  [#14](https://github.com/griptape-ai/griptape-nodes-library-topazlabs/issues/14)
- Topaz Labs nodes report failures on the node with Topaz Labs' reason when it gives one, and put
  the status code, the job or request ID and Topaz Labs' response under **More info**. This covers
  rejected requests, failed jobs, jobs that run past the wait limit, answers missing a job ID,
  request ID, upload URL, ETag or download URL, failed uploads and downloads, timeouts, and dropped
  connections.
  Missing or unreadable inputs and out-of-range values name the parameter as the editor labels it.
  A refused API key (HTTP 401) links to the key in Settings. The messages no longer start with
  prefixes such as "Error during denoising:" or "Unexpected error:".
  [#14](https://github.com/griptape-ai/griptape-nodes-library-topazlabs/issues/14)

[Unreleased]: https://github.com/griptape-ai/griptape-nodes-library-topazlabs/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/griptape-ai/griptape-nodes-library-topazlabs/compare/7e6b49da6249434253105d9e8f916482d3386d64...v0.2.0
