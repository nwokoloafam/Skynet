# Smart suitcase

Planning and future code for a carry-on suitcase that follows a paired user using UWB range and bearing.

## Current baseline

Updated September 13, 2026. The working plan incorporates the team draft review and UWB discussion.

- 60 mm wheels; four-wheel drive controlled as left/right pairs.
- 25 lb total loaded mass assumed, pending confirmation.
- Manual joystick steering and autonomous following.
- Off-the-shelf electronics; custom electronics only if proven necessary.
- Obstacle avoidance deferred until reliable following is demonstrated.

See [the MVP plan](docs/mvp-plan.md) for architecture, calculations, implementation phases, validation, and open decisions.

## Planning documents

- [MVP baseline](docs/mvp-plan.md)
- [Hardware status and next actions](docs/hardware-status.md)
- [Original team draft](docs/reference/initial-team-draft.docx)
- [Draft comparison and proposed revisions](docs/draft-comparison.md)
- [UWB shortlist and bench experiment](docs/uwb-shortlist.md)

The MVP plan is the current source of truth. The comparison explains incorporated corrections; the Word draft is an unchanged historical reference. Specific component choices remain recommendations until selected and tested. Custom electronics remain outside the MVP scope.

Start with UWB bench testing in parallel with small-chassis manual and speed-control work. Qualify a drivetrain for 25 lb separately before suitcase integration; obstacle avoidance is optional and not a prerequisite.

## Repository layout

- `docs/`: planning and design documents.
- Add firmware, software, and hardware integration directories as implementation begins.

No implementation code or hardware selections have been finalized.
