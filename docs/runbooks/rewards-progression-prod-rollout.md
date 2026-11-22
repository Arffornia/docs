# Rewards, crate keys and progression model: production rollout

Scope: move production from website v0.2.0 and mod v1.0.25 to main. Specs: [008](../specs/008-economy-and-rewards.md), [017](../specs/017-progression-model/spec.md), [020](../specs/020-crates-and-keys.md).

Status: plan, nothing executed. Every production write is run by Brian. Agents only read.

## Where production is today

| Part | Production | Main | Source |
|---|---|---|---|
| Website images (backend and nginx) | `v0.2.0` | 134 commits ahead | `infra` `k8s/config/arffornia/website/values.yaml` |
| Mod | `v1.0.25` (released 2026-07-31, the GitHub `latest`) | 91 commits ahead, `mod_version=1.0.25` | `Arffornia_Mods` releases |
| Mod delivery | Provisioning `modList.json` pins `tag: latest`, asset `arffornia.jar`, for server and launcher | same | `Arffornia_Provisioning` `config/{server,launcher}/modList.json` |
| Streak rewards | lucky boxes (`rewards.streak.tiers`) | keys when `REWARDS_STREAK_AS_KEYS=true` | `config/rewards.php` |
| Progression | legacy hand-made graph, no snapshot | snapshot-based model | spec 017 |

Staging (`arffornia-staging`) already runs website main with `REWARDS_STREAK_AS_KEYS=true`.

The Arcane pod could not be inspected for the loaded mod version (exec is not allowed to agents). Check it in step 2.

## Facts that shape the order

- The mod comes from the GitHub `latest` release. Tagging a release ships it to the launcher at the next start and to Arcane at the next pod start.
- Arcane restarts every day (offhours guard sleeps 03:00 to 07:00). A pod start loads the datapack from `GET /api/progression/datapack`.
- The new website datapack carries milestone advancements. A mod without Mods#79 and #80 cannot read them (Website#169, #171). Both are in main after `v1.0.25`.
- The website does not migrate on start (`migrateAndSeedDB.enabled: false`). Migrations are a manual step.
- Pending `lucky_box` rewards stay valid after the switch (spec 020, Migration).
- Keys are only useful once a mod with crates runs on every server that claims rewards. So `REWARDS_STREAK_AS_KEYS` goes last.

## Migrations between v0.2.0 and main

Eight migrations, run in this order by `php artisan migrate --force`.

| # | Migration | What it does | Destructive | Rollback (`down`) |
|---|---|---|---|---|
| 1 | `2026_11_08_000001_add_team_synced_at_to_users_table` | adds `users.team_synced_at` | no | drops the column |
| 2 | `2026_11_09_000001_add_typed_rewards` | adds reward `contents`, `source`, `claim_key`, `claimed_at`, `hold_reason`, `users.last_streak_date`. Replaces the pgsql status CHECK. Sets old `source` to `vote` | yes: `on_hold` rewards become `failed`, pending `streak` rewards become `failed` | drops the columns, restores the CHECK. Does not restore the statuses |
| 3 | `2026_11_09_000002_convert_legacy_reward_commands` | runs `rewards:convert-legacy` on existing rewards | yes: rewrites reward rows | empty `down`: restore from dump |
| 4 | `2026_11_21_000001_add_progression_model` | creates `model_snapshots`, `progression_milestones`, `progression_deliveries`, `progression_events`, `player_playtime`. Adds `key`, `validation`, `effort`, `power`, `source`, `name_fr`, `description_fr` to milestones and similar columns to other tables, `stages.threshold`, `module` | no data loss, additive | drops all of it, including any progress written to the new tables |
| 5 | `2026_11_21_000002_add_progression_evaluated_version` | adds `progressions.evaluated_version` | no | drops the column |
| 6 | `2026_11_22_000001_add_best_streak_to_users_table` | adds `users.best_streak` | no | drops the column |
| 7 | `2026_11_22_000001_create_progression_drafts_table` | creates `progression_drafts` | no | drops the table |
| 8 | `2026_11_22_000002_create_progression_draft_entries_table` | creates `progression_draft_entries` | no | drops the table |

Destructive in practice: 2 and 3. Both only touch reward rows. The dump in step 3 is the only way back for them.

## Config to add in production

File: `infra` `k8s/config/arffornia/website/config.yaml` (ConfigMap `arffornia-website-config`).

| Variable | Value | When | Note |
|---|---|---|---|
| `REWARDS_STREAK_AS_KEYS` | `"true"` | step 13, last | default `false`. Staging already has it |
| `REWARDS_STREAK_TIMEZONE` | leave default `Europe/Paris` | never | day boundary of the streak |
| `SESSION_SERIALIZATION` | leave default `json` | never | existing PHP-serialized session rows may log players out once. Accept it |
| `PROGRESSION_VIEWER` | `off` default. `api` shows `/progression` | optional, after step 11 | staging uses `api`. `PROGRESSION_ICON_BASE` stays default in prod, the renders are local |
| `APP_WEB_DEFAULT_LOCALE`, `APP_API_DEFAULT_LOCALE` | defaults `fr`, `en` | never | |

The streak cycle (day 1 to 6 one `arffornia:streak` key, every 7th day also `arffornia:vote`, every 28th `arffornia:legendary`) lives in `config/rewards.php` under `streak.cycle`. It has no env var. It ships with the image.

## Steps

### Phase A: preparation

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Release the website tag. Confirm the images exist | `git -C Arffornia_Website tag vX.Y.Z origin/main` then push the tag. Check `build-and-push-images.yml` is green and both `:vX.Y.Z` images exist | Brian |
| 2 | Read the current state | `kubectl -n arffornia-server-arcane exec deploy/arffornia-server-arcane-minecraft -c arffornia-server-arcane-minecraft -- ls /data/mods \| grep -i arffornia` | Brian |
| 3 | Back up the website database (logical dump) | `kubectl -n postgres exec postgres-cluster-0 -c postgres -- pg_dump -U postgres -Fc arffornia > arffornia-pre-rollout-$(date +%F).dump` then `pg_restore --list` on the file. Keep it off the cluster | Brian |
| 4 | Confirm WAL archiving is healthy (point-in-time recovery) | check no `PostgresWALArchivingStalled` or `PostgresWALArchivingFailing` alert is firing | Brian |
| 5 | Confirm a world backup from today exists | `ls /backups` in the `mc-backup` container, see [world backups](https://github.com/Arffornia/infra/blob/main/docs/runbooks/arffornia-world-backups.md) | Brian |
| 6 | Check that the new datapack and snapshot code are on staging and that staging passed a full rollout of the same steps on a restored copy | read staging, no command | Brian |

### Phase B: ship in one window (evening, before 03:00)

The window between steps 9 and 12 must be short: a pod restart in it loads the new datapack with the old mod.

| # | Step | Command | Who |
|---|---|---|---|
| 7 | Prepare the infra PR: bump both images to the new tag. Do not touch `REWARDS_STREAK_AS_KEYS` | edit `k8s/config/arffornia/website/values.yaml`, open PR, merge after CI | Brian |
| 8 | Put the site in maintenance | `kubectl -n arffornia-website exec deploy/arffornia-website-chart -c backend -- php artisan down` | Brian |
| 9 | Argo CD syncs the new image. Wait for the pod to be ready | `kubectl -n arffornia-website rollout status deploy/arffornia-website-chart` | Brian |
| 10 | Run migrations | `kubectl -n arffornia-website exec deploy/arffornia-website-chart -c backend -- php artisan migrate --force` | Brian |
| 11 | Dry run, then publish snapshot v1. It moves completed milestones to keys and re-evaluates every player. It refuses if a snapshot already exists | `php artisan progression:snapshot-v1 --dry-run`, read the report, then `php artisan progression:snapshot-v1` (same `kubectl exec` prefix) | Brian |
| 12 | Release the mod: tag the next version on `Arffornia_Mods` main. `build.yml` runs `./gradlew githubRelease` on `v*` tags and the release becomes `latest`. Check the release holds `arffornia.jar` | `git -C Arffornia_Mods tag v1.0.26 origin/main && git push origin v1.0.26` | Brian |
| 13 | Restart Arcane so the pod pulls the new jar and datapack. Watch the log for datapack load and no advancement errors | `kubectl -n arffornia-server-arcane rollout restart deploy/arffornia-server-arcane-minecraft` | Brian |
| 14 | Bring the site back | `php artisan up` (same `kubectl exec` prefix) | Brian |

Provisioning needs no PR for the jar: `modList.json` already pins `tag: latest`. A Provisioning PR is only needed if Brian prefers a fixed tag (see decisions). Provisioning `main` is live for every player, so never mix content and tooling in that PR.

### Phase C: keys and crates

| # | Step | Command | Who |
|---|---|---|---|
| 15 | Place the crates at the prod spawn, from an admin account on Arcane. Ids are `streak`, `vote`, `legendary` plus the kit crates | `/arffornia crate place <id>` at each spot | Brian |
| 16 | Open one crate per type with a test key and check the opening and the refusals | in game | Brian |
| 17 | Enable keys: infra PR setting `REWARDS_STREAK_AS_KEYS: "true"` in `config.yaml`, merge, then restart the website pod | `kubectl -n arffornia-website rollout restart deploy/arffornia-website-chart` | Brian |
| 18 | Claim a streak reward with a test account and check a key arrives | in game | Brian |

## Rollback

| After step | Problem | Rollback |
|---|---|---|
| 7 to 9 | new image misbehaves | revert the infra PR (tag back to `v0.2.0`). Migrations already applied: see step 10 |
| 10 | migration fails midway | `php artisan migrate:rollback --step=N --force`, then revert the image. For migrations 2 and 3 the statuses and converted rewards do not come back: `pg_restore` from the step 3 dump |
| 11 | snapshot publish fails | it is one transaction: nothing is published. Fix the findings and rerun. If published but wrong: restore the database from the dump, since `v1` can only be published once |
| 12 to 13 | new mod breaks servers | delete or demote the `v1.0.26` release so `latest` is `v1.0.25` again, restart Arcane. The datapack from the new website is then incompatible: also revert the website image and restore the database |
| 15 | wrong crate position | break the block as admin and place it again |
| 17 | keys misbehave | set `REWARDS_STREAK_AS_KEYS: "false"`, restart the website. Pending keys stay in the list until claimable. New streak rewards go back to lucky boxes |

Database restore: scale the website to zero, `pg_restore --clean --if-exists -d arffornia <dump>` on the master, scale back. WAL-G point-in-time recovery is the fallback if the dump is bad.

## Decisions for Brian

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | Pin the mod in Provisioning | keep `latest` (zero change, release equals ship) or pin `v1.0.26` in `modList.json` for server only | keep `latest` for now. Release only inside the window |
| 2 | Spawn crate positions | coordinates of the shop area | needed before step 15 |
| 3 | Maintenance window | evening before 03:00 | evening |
| 4 | Session logout on `SESSION_SERIALIZATION=json` | accept or force `php` in the ConfigMap | accept |

## Open checks

- Whether mod v1.0.25 tolerates the new website API during steps 9 to 12 was not verified. Test on staging with the old jar if the window cannot be kept short.
- Only `/arffornia crate place <id>` is documented (spec 020). The crate ids beyond streak, vote and legendary were not listed.
