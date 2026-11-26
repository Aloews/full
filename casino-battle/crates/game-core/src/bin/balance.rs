use std::{env, process};

use casino_battle_core::RunState;

fn main() {
    let seeds = env::args()
        .nth(1)
        .map(|value| {
            value.parse::<u64>().unwrap_or_else(|_| {
                eprintln!("Usage: cargo run -p casino-battle-core --bin balance -- [seed-count]");
                process::exit(2);
            })
        })
        .unwrap_or(5_000);

    if seeds == 0 || seeds > 1_000_000 {
        eprintln!("Seed count must be between 1 and 1,000,000.");
        process::exit(2);
    }

    let mut total_draws = 0_u64;
    let mut draws_with_clusters = 0_u64;
    let mut total_clusters = 0_u64;
    let mut clusters_3_4 = 0_u64;
    let mut clusters_5_7 = 0_u64;
    let mut clusters_8_plus = 0_u64;
    let mut rank_one = 0_u64;
    let mut rank_two = 0_u64;
    let mut rank_three = 0_u64;
    let mut capped_party_draws = 0_u64;
    let mut total_battle_ticks = 0_u64;
    let mut battle_wins = 0_u64;
    let mut battle_losses = 0_u64;

    for seed in 1..=seeds {
        let mut run = RunState::new(seed);
        let mut capped_this_run = false;

        for _ in 0..5 {
            let outcome = run.draw().expect("five starting draws must be affordable");
            total_draws += 1;

            if !outcome.matches.is_empty() {
                draws_with_clusters += 1;
            }

            for cluster in outcome.matches {
                total_clusters += 1;
                match cluster.size {
                    3..=4 => clusters_3_4 += 1,
                    5..=7 => clusters_5_7 += 1,
                    _ => clusters_8_plus += 1,
                }
            }

            for unit in outcome.recruited {
                match unit.rank {
                    1 => rank_one += 1,
                    2 => rank_two += 1,
                    _ => rank_three += 1,
                }
            }

            if outcome.party_size == 6 {
                capped_this_run = true;
            }
        }

        if capped_this_run {
            capped_party_draws += 1;
        }

        if let Ok(report) = run.resolve_auto_battle() {
            total_battle_ticks += u64::from(report.ticks);
            if report.victory {
                battle_wins += 1;
            } else {
                battle_losses += 1;
            }
        }
    }

    let percent = |value: u64, total: u64| {
        if total == 0 {
            0.0
        } else {
            value as f64 * 100.0 / total as f64
        }
    };

    println!("Casino Battle deterministic balance sample");
    println!("Seeds: {seeds}");
    println!("Fate draws: {total_draws}");
    println!(
        "Draws with at least one cluster: {} ({:.2}%)",
        draws_with_clusters,
        percent(draws_with_clusters, total_draws)
    );
    println!("Clusters: {total_clusters}");
    println!(
        "Cluster sizes: 3-4={} ({:.2}%), 5-7={} ({:.2}%), 8+={} ({:.2}%)",
        clusters_3_4,
        percent(clusters_3_4, total_clusters),
        clusters_5_7,
        percent(clusters_5_7, total_clusters),
        clusters_8_plus,
        percent(clusters_8_plus, total_clusters)
    );
    println!(
        "Recruits by rank: I={rank_one}, II={rank_two}, III={rank_three}"
    );
    println!(
        "Runs reaching party cap: {} ({:.2}%)",
        capped_party_draws,
        percent(capped_party_draws, seeds)
    );
    println!(
        "Auto-battle result: wins={battle_wins} ({:.2}%), losses={battle_losses} ({:.2}%), avg ticks={:.2}",
        percent(battle_wins, seeds),
        percent(battle_losses, seeds),
        total_battle_ticks as f64 / seeds as f64
    );
}
