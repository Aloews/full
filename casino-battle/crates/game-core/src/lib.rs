use std::collections::VecDeque;

use serde::{Deserialize, Serialize};
use thiserror::Error;

const BOARD_SIZE: usize = 4;
const PARTY_LIMIT: usize = 6;
const MAX_BATTLE_TICKS: u32 = 240;

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Sigil {
    Leaf,
    Ember,
    Tide,
    Stone,
    Moon,
    Wing,
}

impl Sigil {
    const ALL: [Self; 6] = [
        Self::Leaf,
        Self::Ember,
        Self::Tide,
        Self::Stone,
        Self::Moon,
        Self::Wing,
    ];

    fn from_index(index: usize) -> Self {
        Self::ALL[index % Self::ALL.len()]
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Role {
    Guardian,
    Striker,
    Support,
    Mystic,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RunPhase {
    Preparation,
    RunOver,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SynergyTier {
    Budding,
    Flourishing,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct SynergyStatus {
    pub sigil: Sigil,
    pub unit_count: usize,
    pub tier: SynergyTier,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct Unit {
    pub id: u64,
    pub name: String,
    pub sigil: Sigil,
    pub role: Role,
    pub lane: u8,
    pub hp: i32,
    pub max_hp: i32,
    pub attack: i32,
    pub armor: i32,
    pub attack_cooldown: u32,
    pub cooldown_left: u32,
    pub rank: u8,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SigilCluster {
    pub sigil: Sigil,
    pub size: u8,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct RunState {
    pub seed: u64,
    rng_state: u64,
    pub phase: RunPhase,
    pub wave: u32,
    pub essence: u32,
    pub hearts: u8,
    next_unit_id: u64,
    pub board: [[Sigil; BOARD_SIZE]; BOARD_SIZE],
    pub party: Vec<Unit>,
    pub total_draws: u32,
    pub battle_wins: u32,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct DrawOutcome {
    pub board: [[Sigil; BOARD_SIZE]; BOARD_SIZE],
    pub matches: Vec<SigilCluster>,
    pub recruited: Vec<Unit>,
    pub essence_left: u32,
    pub party_size: usize,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BattleEventKind {
    Attack,
    Heal,
    Defeat,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BattleEvent {
    pub tick: u32,
    pub kind: BattleEventKind,
    pub source_unit_id: u64,
    pub target_unit_id: u64,
    pub amount: u32,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct BattleReport {
    pub victory: bool,
    pub ticks: u32,
    pub wave: u32,
    pub surviving_allies: usize,
    pub surviving_enemies: usize,
    pub hearts_left: u8,
    pub essence_reward: u32,
    pub events: Vec<BattleEvent>,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum GameError {
    #[error("the run is no longer active")]
    RunOver,
    #[error("not enough essence for a fate draw")]
    NotEnoughEssence,
    #[error("a battle cannot be started with an empty party")]
    EmptyParty,
    #[error("one or both selected units were not found")]
    UnitNotFound,
    #[error("units must share a sigil and rank, and the keeper must be below rank 3")]
    InvalidMerge,
}

impl RunState {
    pub fn new(seed: u64) -> Self {
        let mut state = Self {
            seed,
            rng_state: seed.max(1),
            phase: RunPhase::Preparation,
            wave: 1,
            essence: 5,
            hearts: 3,
            next_unit_id: 1,
            board: [[Sigil::Leaf; BOARD_SIZE]; BOARD_SIZE],
            party: Vec::new(),
            total_draws: 0,
            battle_wins: 0,
        };
        let starter = state.make_unit(Sigil::Leaf, 1);
        state.party.push(starter);
        state
    }

    pub fn synergies(&self) -> Vec<SynergyStatus> {
        Sigil::ALL
            .iter()
            .filter_map(|sigil| {
                let unit_count = self
                    .party
                    .iter()
                    .filter(|unit| unit.hp > 0 && unit.sigil == *sigil)
                    .count();
                (unit_count >= 2).then_some(SynergyStatus {
                    sigil: *sigil,
                    unit_count,
                    tier: if unit_count >= 4 {
                        SynergyTier::Flourishing
                    } else {
                        SynergyTier::Budding
                    },
                })
            })
            .collect()
    }

    pub fn merge_units(&mut self, keeper_id: u64, donor_id: u64) -> Result<(), GameError> {
        self.ensure_preparation()?;
        if keeper_id == donor_id {
            return Err(GameError::InvalidMerge);
        }

        let keeper_index = self
            .party
            .iter()
            .position(|unit| unit.id == keeper_id)
            .ok_or(GameError::UnitNotFound)?;
        let donor_index = self
            .party
            .iter()
            .position(|unit| unit.id == donor_id)
            .ok_or(GameError::UnitNotFound)?;

        let keeper = &self.party[keeper_index];
        let donor = &self.party[donor_index];
        if keeper.sigil != donor.sigil || keeper.rank != donor.rank || keeper.rank >= 3 {
            return Err(GameError::InvalidMerge);
        }

        let _donor = self.party.remove(donor_index);
        let adjusted_keeper_index = if donor_index < keeper_index {
            keeper_index - 1
        } else {
            keeper_index
        };
        let keeper = &mut self.party[adjusted_keeper_index];
        keeper.rank += 1;
        keeper.max_hp += 5;
        keeper.hp = (keeper.hp + 5).min(keeper.max_hp);
        keeper.attack += 2;
        keeper.armor += 1;
        keeper.cooldown_left = 0;
        Ok(())
    }

    pub fn draw(&mut self) -> Result<DrawOutcome, GameError> {
        self.ensure_preparation()?;
        if self.essence == 0 {
            return Err(GameError::NotEnoughEssence);
        }

        self.essence -= 1;
        self.total_draws += 1;

        for row in 0..BOARD_SIZE {
            for col in 0..BOARD_SIZE {
                self.board[row][col] = Sigil::from_index(self.random_index(Sigil::ALL.len()));
            }
        }

        let matches = self.find_matches();
        let mut recruited = Vec::new();
        for cluster in matches.iter().copied() {
            let rank = Self::rank_for_cluster(cluster.size);
            if self.party.len() >= PARTY_LIMIT {
                self.essence = self
                    .essence
                    .saturating_add(1 + u32::from(cluster.size.saturating_sub(3)) / 3);
                continue;
            }

            let unit = self.make_unit(cluster.sigil, rank);
            recruited.push(unit.clone());
            self.party.push(unit);
            if cluster.size >= 8 {
                self.essence = self.essence.saturating_add(1);
            }
        }

        Ok(DrawOutcome {
            board: self.board,
            matches,
            recruited,
            essence_left: self.essence,
            party_size: self.party.len(),
        })
    }

    pub fn resolve_auto_battle(&mut self) -> Result<BattleReport, GameError> {
        self.ensure_preparation()?;
        if self.party.iter().all(|unit| unit.hp <= 0) {
            return Err(GameError::EmptyParty);
        }

        let mut enemies = self.create_enemy_wave();
        let mut ticks = 0;
        let mut events = Vec::new();

        while ticks < MAX_BATTLE_TICKS
            && self.party.iter().any(|unit| unit.hp > 0)
            && enemies.iter().any(|unit| unit.hp > 0)
        {
            ticks += 1;
            events.extend(Self::advance_side(&mut self.party, &mut enemies, ticks));
            events.extend(Self::advance_side(&mut enemies, &mut self.party, ticks));
        }

        let surviving_allies = self.party.iter().filter(|unit| unit.hp > 0).count();
        let surviving_enemies = enemies.iter().filter(|unit| unit.hp > 0).count();
        let victory = surviving_enemies == 0 && surviving_allies > 0;
        let essence_reward = if victory { 2 + self.wave / 3 } else { 0 };

        if victory {
            self.battle_wins += 1;
            self.wave += 1;
            self.essence += essence_reward;
            for unit in &mut self.party {
                if unit.hp > 0 {
                    unit.hp = (unit.hp + 2).min(unit.max_hp);
                }
            }
        } else {
            self.hearts = self.hearts.saturating_sub(1);
            if self.hearts == 0 {
                self.phase = RunPhase::RunOver;
            } else {
                for unit in &mut self.party {
                    unit.hp = unit.max_hp.max(1);
                    unit.cooldown_left = 0;
                }
            }
        }

        Ok(BattleReport {
            victory,
            ticks,
            wave: self.wave,
            surviving_allies,
            surviving_enemies,
            hearts_left: self.hearts,
            essence_reward,
            events,
        })
    }

    fn ensure_preparation(&self) -> Result<(), GameError> {
        if self.phase == RunPhase::RunOver {
            Err(GameError::RunOver)
        } else {
            Ok(())
        }
    }

    fn find_matches(&self) -> Vec<SigilCluster> {
        let mut visited = [[false; BOARD_SIZE]; BOARD_SIZE];
        let mut clusters = Vec::new();
        let directions = [(-1_i32, 0_i32), (1, 0), (0, -1), (0, 1)];

        for row in 0..BOARD_SIZE {
            for col in 0..BOARD_SIZE {
                if visited[row][col] {
                    continue;
                }

                let sigil = self.board[row][col];
                let mut queue = VecDeque::from([(row, col)]);
                let mut cluster_size = 0_u8;
                visited[row][col] = true;

                while let Some((current_row, current_col)) = queue.pop_front() {
                    cluster_size = cluster_size.saturating_add(1);
                    for (row_delta, col_delta) in directions {
                        let next_row = current_row as i32 + row_delta;
                        let next_col = current_col as i32 + col_delta;
                        if next_row < 0
                            || next_col < 0
                            || next_row >= BOARD_SIZE as i32
                            || next_col >= BOARD_SIZE as i32
                        {
                            continue;
                        }

                        let next_row = next_row as usize;
                        let next_col = next_col as usize;
                        if !visited[next_row][next_col] && self.board[next_row][next_col] == sigil {
                            visited[next_row][next_col] = true;
                            queue.push_back((next_row, next_col));
                        }
                    }
                }

                if cluster_size >= 3 {
                    clusters.push(SigilCluster {
                        sigil,
                        size: cluster_size,
                    });
                }
            }
        }

        clusters
    }

    fn rank_for_cluster(size: u8) -> u8 {
        match size {
            8.. => 3,
            5..=7 => 2,
            _ => 1,
        }
    }

    fn make_unit(&mut self, sigil: Sigil, rank: u8) -> Unit {
        let (name, role, hp, attack, armor, cooldown) = match sigil {
            Sigil::Leaf => ("Mossguard", Role::Guardian, 26, 4, 3, 3),
            Sigil::Ember => ("Cinderkit", Role::Striker, 15, 8, 0, 2),
            Sigil::Tide => ("Puddlekin", Role::Support, 20, 4, 1, 3),
            Sigil::Stone => ("Pebbleback", Role::Guardian, 30, 3, 4, 4),
            Sigil::Moon => ("Moonmote", Role::Mystic, 16, 7, 0, 3),
            Sigil::Wing => ("Breezeling", Role::Striker, 17, 6, 1, 2),
        };
        let multiplier = i32::from(rank.saturating_sub(1));
        let lane = (self.party.len() % 3) as u8;
        let unit = Unit {
            id: self.next_unit_id,
            name: name.to_owned(),
            sigil,
            role,
            lane,
            hp: hp + multiplier * 5,
            max_hp: hp + multiplier * 5,
            attack: attack + multiplier * 2,
            armor: armor + multiplier,
            attack_cooldown: cooldown.max(1),
            cooldown_left: 0,
            rank,
        };
        self.next_unit_id += 1;
        unit
    }

    fn create_enemy_wave(&mut self) -> Vec<Unit> {
        let count = (1 + self.wave as usize / 2).clamp(1, 5);
        (0..count)
            .map(|index| {
                let sigil = Sigil::from_index(self.random_index(Sigil::ALL.len()));
                let base_hp = 10 + self.wave as i32 * 3 + index as i32 * 2;
                let unit = Unit {
                    id: u64::MAX - index as u64,
                    name: format!("Gloomling {}", index + 1),
                    sigil,
                    role: match sigil {
                        Sigil::Leaf | Sigil::Stone => Role::Guardian,
                        Sigil::Ember | Sigil::Wing => Role::Striker,
                        Sigil::Tide => Role::Support,
                        Sigil::Moon => Role::Mystic,
                    },
                    lane: (index % 3) as u8,
                    hp: base_hp,
                    max_hp: base_hp,
                    attack: 2 + self.wave as i32,
                    armor: (self.wave / 4) as i32,
                    attack_cooldown: 3,
                    cooldown_left: 0,
                    rank: 1,
                };
                unit
            })
            .collect()
    }

    fn advance_side(attackers: &mut [Unit], defenders: &mut [Unit], tick: u32) -> Vec<BattleEvent> {
        let mut events = Vec::new();

        for attacker_index in 0..attackers.len() {
            if attackers[attacker_index].hp <= 0 {
                continue;
            }
            if attackers[attacker_index].cooldown_left > 0 {
                attackers[attacker_index].cooldown_left -= 1;
                continue;
            }

            let source_id = attackers[attacker_index].id;
            let role = attackers[attacker_index].role;
            let lane = attackers[attacker_index].lane;

            if role == Role::Support {
                let heal_target = attackers
                    .iter()
                    .enumerate()
                    .filter(|(index, unit)| {
                        *index != attacker_index && unit.hp > 0 && unit.hp < unit.max_hp
                    })
                    .min_by_key(|(_, unit)| {
                        (i64::from(unit.hp) * 100) / i64::from(unit.max_hp.max(1))
                    })
                    .map(|(index, _)| index);

                if let Some(target_index) = heal_target {
                    let heal_amount = 3 + u32::from(attackers[attacker_index].rank);
                    let target = &mut attackers[target_index];
                    let healed = (target.max_hp - target.hp).min(heal_amount as i32);
                    target.hp += healed;
                    let target_id = target.id;
                    attackers[attacker_index].cooldown_left =
                        attackers[attacker_index].attack_cooldown;
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::Heal,
                        source_unit_id: source_id,
                        target_unit_id: target_id,
                        amount: healed as u32,
                    });
                    continue;
                }
            }

            let target_index = defenders
                .iter()
                .enumerate()
                .filter(|(_, unit)| unit.hp > 0)
                .min_by_key(|(_, unit)| lane.abs_diff(unit.lane))
                .map(|(index, _)| index);

            if let Some(target_index) = target_index {
                let bonus = match role {
                    Role::Striker => 2,
                    Role::Mystic => 1,
                    Role::Guardian | Role::Support => 0,
                };
                let attack = attackers[attacker_index].attack + bonus;
                let target = &mut defenders[target_index];
                let damage = (attack - target.armor).max(1);
                target.hp = (target.hp - damage).max(0);
                let target_id = target.id;
                let defeated = target.hp == 0;
                events.push(BattleEvent {
                    tick,
                    kind: BattleEventKind::Attack,
                    source_unit_id: source_id,
                    target_unit_id: target_id,
                    amount: damage as u32,
                });
                if defeated {
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::Defeat,
                        source_unit_id: source_id,
                        target_unit_id: target_id,
                        amount: 0,
                    });
                }

                if role == Role::Mystic {
                    let splash_index = defenders
                        .iter()
                        .enumerate()
                        .filter(|(index, unit)| *index != target_index && unit.hp > 0)
                        .min_by_key(|(_, unit)| lane.abs_diff(unit.lane))
                        .map(|(index, _)| index);
                    if let Some(splash_index) = splash_index {
                        let splash = &mut defenders[splash_index];
                        let splash_damage = (damage / 2).max(1);
                        splash.hp = (splash.hp - splash_damage).max(0);
                        let splash_id = splash.id;
                        let splash_defeated = splash.hp == 0;
                        events.push(BattleEvent {
                            tick,
                            kind: BattleEventKind::Attack,
                            source_unit_id: source_id,
                            target_unit_id: splash_id,
                            amount: splash_damage as u32,
                        });
                        if splash_defeated {
                            events.push(BattleEvent {
                                tick,
                                kind: BattleEventKind::Defeat,
                                source_unit_id: source_id,
                                target_unit_id: splash_id,
                                amount: 0,
                            });
                        }
                    }
                }

                attackers[attacker_index].cooldown_left = attackers[attacker_index].attack_cooldown;
            }
        }

        events
    }
    fn random_u64(&mut self) -> u64 {
        self.rng_state ^= self.rng_state >> 12;
        self.rng_state ^= self.rng_state << 25;
        self.rng_state ^= self.rng_state >> 27;
        self.rng_state.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    fn random_index(&mut self, upper: usize) -> usize {
        let bound = upper as u64;
        let rejection_threshold = bound.wrapping_neg() % bound;
        loop {
            let value = self.random_u64();
            if value >= rejection_threshold {
                return (value % bound) as usize;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn same_seed_produces_same_draw_sequence() {
        let mut left = RunState::new(42);
        let mut right = RunState::new(42);
        for _ in 0..3 {
            assert_eq!(left.draw().unwrap(), right.draw().unwrap());
        }
        assert_eq!(left, right);
    }

    #[test]
    fn draw_consumes_essence_and_resolves_connected_clusters() {
        let mut run = RunState::new(7);
        let start = run.essence;
        let result = run.draw().unwrap();
        assert_eq!(run.essence, result.essence_left);
        assert!(run.essence <= start + 8);
        assert!(run.party.len() <= PARTY_LIMIT);
        assert!(result.matches.iter().all(|cluster| cluster.size >= 3));
    }

    #[test]
    fn fate_board_matches_connected_shapes_not_paylines() {
        let mut run = RunState::new(77);
        run.board = [
            [Sigil::Ember, Sigil::Ember, Sigil::Ember, Sigil::Tide],
            [Sigil::Ember, Sigil::Ember, Sigil::Tide, Sigil::Stone],
            [Sigil::Moon, Sigil::Tide, Sigil::Stone, Sigil::Wing],
            [Sigil::Stone, Sigil::Moon, Sigil::Wing, Sigil::Leaf],
        ];

        let matches = run.find_matches();
        assert_eq!(
            matches,
            vec![SigilCluster {
                sigil: Sigil::Ember,
                size: 5
            }]
        );
    }

    #[test]
    fn cluster_size_controls_recruit_rank() {
        assert_eq!(RunState::rank_for_cluster(3), 1);
        assert_eq!(RunState::rank_for_cluster(4), 1);
        assert_eq!(RunState::rank_for_cluster(5), 2);
        assert_eq!(RunState::rank_for_cluster(7), 2);
        assert_eq!(RunState::rank_for_cluster(8), 3);
        assert_eq!(RunState::rank_for_cluster(16), 3);
    }

    #[test]
    fn battle_is_automatic_and_advances_the_run() {
        let mut run = RunState::new(99);
        let result = run.resolve_auto_battle().unwrap();
        assert!(result.ticks <= MAX_BATTLE_TICKS);
        assert!(result.surviving_allies <= PARTY_LIMIT);
        assert!(run.wave >= 1);
    }

    #[test]
    fn cannot_draw_without_essence() {
        let mut run = RunState::new(123);
        run.essence = 0;
        assert_eq!(run.draw(), Err(GameError::NotEnoughEssence));
    }

    #[test]
    fn duplicate_units_merge_into_a_stronger_rank() {
        let mut run = RunState::new(5);
        let keeper_id = run.party[0].id;
        let mut donor = run.party[0].clone();
        donor.id = 900;
        run.party.push(donor);

        assert_eq!(run.synergies()[0].tier, SynergyTier::Budding);
        run.merge_units(keeper_id, 900).unwrap();

        assert_eq!(run.party.len(), 1);
        assert_eq!(run.party[0].rank, 2);
        assert_eq!(run.party[0].max_hp, 31);
        assert_eq!(run.party[0].attack, 6);
    }

    #[test]
    fn invalid_merge_does_not_change_the_party() {
        let mut run = RunState::new(6);
        let before = run.party.clone();
        assert_eq!(run.merge_units(1, 999), Err(GameError::UnitNotFound));
        assert_eq!(run.party, before);

        let mut other = run.party[0].clone();
        other.id = 2;
        other.sigil = Sigil::Ember;
        run.party.push(other);
        let before = run.party.clone();
        assert_eq!(run.merge_units(1, 2), Err(GameError::InvalidMerge));
        assert_eq!(run.party, before);
    }

    #[test]
    fn four_matching_units_unlock_a_higher_synergy_tier() {
        let mut run = RunState::new(7);
        for id in 10..13 {
            let mut unit = run.party[0].clone();
            unit.id = id;
            run.party.push(unit);
        }
        let synergies = run.synergies();
        assert_eq!(synergies.len(), 1);
        assert_eq!(synergies[0].unit_count, 4);
        assert_eq!(synergies[0].tier, SynergyTier::Flourishing);
    }

    #[test]
    fn auto_battle_targets_the_nearest_lane() {
        let run = RunState::new(8);
        let mut attacker = run.party[0].clone();
        attacker.lane = 1;
        attacker.attack = 5;
        attacker.cooldown_left = 0;

        let mut far_target = attacker.clone();
        far_target.id = 100;
        far_target.lane = 2;
        far_target.hp = 20;
        far_target.armor = 0;

        let mut near_target = attacker.clone();
        near_target.id = 101;
        near_target.lane = 1;
        near_target.hp = 20;
        near_target.armor = 0;

        let mut attackers = vec![attacker];
        let mut defenders = vec![far_target, near_target];
        RunState::advance_side(&mut attackers, &mut defenders, 1);

        assert_eq!(defenders[0].hp, 20);
        assert_eq!(defenders[1].hp, 15);
    }

    #[test]
    fn support_units_heal_the_most_wounded_ally() {
        let mut support = RunState::new(31).party[0].clone();
        support.id = 1;
        support.role = Role::Support;
        support.hp = 10;

        let mut wounded = support.clone();
        wounded.id = 2;
        wounded.role = Role::Striker;
        wounded.hp = 5;
        wounded.max_hp = 20;

        let mut healthy = support.clone();
        healthy.id = 3;
        healthy.role = Role::Guardian;
        healthy.hp = 20;
        healthy.max_hp = 26;

        let mut allies = vec![support, wounded, healthy];
        let mut enemies = vec![];
        let events = RunState::advance_side(&mut allies, &mut enemies, 1);

        assert_eq!(allies[1].hp, 9);
        assert_eq!(allies[2].hp, 20);
        assert_eq!(events[0].kind, BattleEventKind::Heal);
        assert_eq!(events[0].target_unit_id, 2);
    }

    #[test]
    fn mystic_splashes_damage_to_a_second_target() {
        let mut mystic = RunState::new(32).party[0].clone();
        mystic.id = 1;
        mystic.role = Role::Mystic;
        mystic.attack = 6;
        mystic.lane = 1;

        let mut first = mystic.clone();
        first.id = 100;
        first.role = Role::Striker;
        first.hp = 20;
        first.max_hp = 20;
        first.armor = 0;
        first.lane = 1;

        let mut second = first.clone();
        second.id = 101;
        second.lane = 2;

        let mut attackers = vec![mystic];
        let mut defenders = vec![first, second];
        let events = RunState::advance_side(&mut attackers, &mut defenders, 1);

        assert_eq!(defenders[0].hp, 13);
        assert_eq!(defenders[1].hp, 17);
        assert_eq!(events.len(), 2);
        assert!(events
            .iter()
            .all(|event| event.kind == BattleEventKind::Attack));
    }

    #[test]
    fn defeated_run_rejects_future_actions() {
        let mut run = RunState::new(1);
        run.hearts = 0;
        run.phase = RunPhase::RunOver;
        assert_eq!(run.draw(), Err(GameError::RunOver));
        assert_eq!(run.resolve_auto_battle(), Err(GameError::RunOver));
        assert_eq!(run.merge_units(1, 2), Err(GameError::RunOver));
    }
}
