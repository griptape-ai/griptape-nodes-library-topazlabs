- **Breaking:** a missing `TOPAZ_LABS_API_KEY` is reported when the node runs, on the node, with a
  link to the key in Settings, and no longer when the flow starts. Nodes upstream of a Topaz Labs
  node run first. The key is reported on its own, before any other problem. Out-of-range values on
  the denoise, enhance and video nodes are also reported when the node runs, not at flow start.
  [#14](https://github.com/griptape-ai/griptape-nodes-library-topazlabs/issues/14)
