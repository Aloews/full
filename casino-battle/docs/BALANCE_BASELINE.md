# Initial balance baseline

**Sample:** 1,000 deterministic run seeds  
**Build:** first wave, five Fate Board draws per run, one automatic battle per run  
**Verified by:** GitHub Actions run 45889366014, commit `9362c28b291a402cc297724f8cf1123cf380aae0`

## Results

| Metric | Observed |
|---|---:|
| Fate draws | 5,000 |
| Draws with at least one connected cluster | 3,289 / 5,000 (65.78%) |
| Connected clusters | 4,271 |
| Cluster size 3–4 | 3,844 (90.00%) |
| Cluster size 5–7 | 418 (9.79%) |
| Cluster size 8+ | 9 (0.21%) |
| Rank I recruits | 3,527 |
| Rank II recruits | 391 |
| Rank III recruits | 7 |
| Runs reaching the six-unit party cap | 437 / 1,000 (43.70%) |
| First-wave Auto-battle wins | 931 / 1,000 (93.10%) |
| First-wave Auto-battle losses | 69 / 1,000 (6.90%) |
| Average Auto-battle ticks | 10.16 |

## Interpretation

- The connected-cluster rule produces a recruit on roughly two thirds of draw attempts in this sample.
- Rank III remains rare in the current uniform six-sigil board.
- The six-unit party cap is reached in fewer than half of runs after five draws, so roster overflow is present but not universal.
- The first wave is intentionally approachable but is not a guaranteed win: 6.90% of these seeded runs lost.
- The median build and survival curve have not yet been measured. This sample covers only the first fight and does not establish late-run balance.

## Next balance gates

1. Run 10,000+ seeds across a complete multi-wave run.
2. Report victory/loss rate by wave, not only an aggregate.
3. Compare each role and sigil synergy with ablation runs.
4. Measure rank distribution, empty-draw streaks and roster saturation.
5. Adjust only from reproducible reports and keep the baseline commit with each result.
