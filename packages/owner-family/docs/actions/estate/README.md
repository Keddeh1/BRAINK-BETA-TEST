# Call admitted owner MCP estate tools

## Function and architectural application

Invoke only exposed tools: estate_status, mesh_discover, mesh_status, mesh_aggregate, mesh_verify_evidence, host_agent_capabilities, lexicon_stats, bilateral_summary and dependency_frontier.

## User guidelines

Use existing owner tool identities; mesh_read_status aliases mesh_status. Arbitrary shell and nonadmitted side-effect tools are not exposed.

## Entry and expected context

`POST /api/web4/control {action: estate, tool: mesh_status, arguments: {}}`

## Fit, case and field use

Read live mesh aggregation or bilateral capability relationships through the supplied MCP implementation.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
