- Topaz Labs nodes report failures on the node with Topaz Labs' reason when it gives one, and put
  the status code, the job or request ID and Topaz Labs' response under **More info**. This covers rejected
  requests, failed jobs, jobs that run past the wait limit, answers missing a job ID, request ID,
  upload URL, ETag or download URL, failed uploads and downloads, timeouts, and dropped connections.
  Missing or unreadable inputs and out-of-range values name the parameter as the editor labels it.
  A refused API key (HTTP 401) links to the key in Settings. The messages no longer start with
  prefixes such as "Error during denoising:" or "Unexpected error:".
  [#14](https://github.com/griptape-ai/griptape-nodes-library-topazlabs/issues/14)
