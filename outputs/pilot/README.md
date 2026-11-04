# Pilot runs (50 self-generated maps, gpt-4o-mini)

Inputs: `dataset/generated/pilot.json` (`python -m llmastar.quorumastar.pilot make`). These runs chose the defaults
(agent.md Decisions, 2026-11-04); the evaluation maps never did.

Run names list the settings that differ from the default *at the time of the run*. Every run here was made while the
vision judge was on by default, so a name without `-novision` had the judge:

| run | views | judge |
|---|---|---|
| `quorumastar-vtext+corners+image+relations` | text, corners, image, relations | yes |
| `quorumastar-vtext+corners+image+relations-novision` | the same four | no |
| `quorumastar-vtext+corners+image+relations-rm0` | the same four, no removal step | no (the judge only runs with removal) |
| `quorumastar-vtext+corners+relations` and `quorumastar` (rerun 2026-11-04 10:41) | text, corners, relations | yes |
| `quorumastar-novision` | text, corners, relations | no (today's default) |

`pilot_<run>.md` is `pilot report` for that run; `analysis.md` is `python -m llmastar.analysis` on this folder.
