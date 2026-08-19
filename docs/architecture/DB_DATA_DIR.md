# SISTER_DB_DATA_DIR compatibility contract

## Scope

OPS-002B teaches SisTer to use an explicit host directory for PostgreSQL
persistence when `SISTER_DB_DATA_DIR` is configured.

This is an incremental compatibility layer. It does **not** migrate the
currently installed operational database and it does not change the legacy
default.

## Legacy behavior

When `SISTER_DB_DATA_DIR` is absent, SisTer keeps the existing named-volume
contract. The current installed runtime therefore remains compatible without
any configuration change.

## Explicit data directory

When `SISTER_DB_DATA_DIR` is present, it must be an absolute host path.
SisTer uses it as the source of `/var/lib/postgresql/data` through Podman.
The directory is created only when the database is explicitly started.

## Safety guard

Before `up`, `down`, or `destroy` touches an existing container while
`SISTER_DB_DATA_DIR` is active, SisTer inspects the container's current
`/var/lib/postgresql/data` mount. If the existing container points to another
host path, the operation fails before replacing, stopping, or removing it.

This prevents a future DEVELOPMENT or CANDIDATE command from accidentally
touching the legacy operational database merely because a container name was
reused.

## Destruction semantics

Legacy named-volume mode keeps its historical destroy behavior.

With explicit bind-mounted storage, `destroy.sh` removes only the matching
container and preserves the host data directory. Deleting bind-mounted
PostgreSQL data requires a separate explicit data-plane operation.

## Compose boundary

In OPS-002B, explicit `SISTER_DB_DATA_DIR` uses the Podman execution path.
The existing Compose path remains unchanged for legacy named-volume mode.

## Planned consumers

`sister-infra` will provide paths such as:

```text
development:
  ~/.local/share/sister-data/development/sister/postgres

candidate:
  ~/.local/share/sister-data/candidate/<candidate-id>/sister/postgres

operational:
  ~/.local/share/sister-data/operational/sister/postgres
```

OPS-002B only provides the SisTer-side capability. Path selection belongs to
deployment orchestration.
