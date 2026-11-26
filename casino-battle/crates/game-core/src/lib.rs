use serde::{Deserialize, Serialize};
use thiserror::Error;

const BOARD_SIZE: usize = 3;
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
    pub matches: Vec<Sigil>,
    pub recruited: Vec<Unit>,
    pub essence_left: u32,
    pub party_size: usize,
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

        let keeper_index = self.party.iter().position(|unit| unit.id == keeper_id)
            .ok_or(GameError::UnitNotFound)?;
        let donor_index = self.party.iter().position(|unit| unit.id == donor_id)
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
        for sigil in matches.iter().copied() {
            if self.party.len() >= PARTY_LIMIT {
                self.essence += 1;
                continue;
            }

            let unit = self.make_unit(sigil, 1);
            recruited.push(unit.clone());
            self.party.push(unit);
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

        while ticks < MAX_BATTLE_TICKS
            && self.party.iter().any(|unit| unit.hp > 0)
            && enemies.iter().any(|unit| unit.hp > 0)
        {
            Self::advance_side(&mut self.party, &mut enemies);
            Self::advance_side(&mut enemies, &mut self.party);
            ticks += 1;
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
        })
    }

    fn ensure_preparation(&self) -> Result<(), GameError> {
        if self.phase == RunPhase::RunOver {
            Err(GameError::RunOver)
        } else {
            Ok(())
        }
    }

    fn find_matches(&self) -> Vec<Sigil> {
        let lines: [[(usize, usize); BOARD_SIZE]; 8] = [
            [(0, 0), (0, 1), (0, 2)],
            [(1, 0), (1, 1), (1, 2)],
            [(2, 0), (2, 1), (2, 2)],
            [(0, 0), (1, 0), (2, 0)],
            [(0, 1), (1, 1), (2, 1)],
            [(0, 2), (1, 2), (2, 2)],
            [(0, 0), (1, 1), (2, 2)],
            [(0, 2), (1, 1), (2, 0)],
        ];

        lines
            .iter()
            .filter_map(|line| {
                let first = self.board[line[0].0][line[0].1];
                line.iter()
                    .all(|(row, col)| self.board[*row][*col] == first)
                    .then_some(first)
            })
            .collect()
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
                    role: Role::Striker,
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

    fn advance_side(attackers: &mut [Unit], defenders: &mut [Unit]) {
        for attacker in attackers.iter_mut().filter(|unit| unit.hp > 0) {
            if attacker.cooldown_left > 0 {
                attacker.cooldown_left -= 1;
                continue;
            }
            let target_index = defenders
                .iter()
                .enumerate()
                .filter(|(_, unit)| unit.hp > 0)
                .min_by_key(|(_, unit)| attacker.lane.abs_diff(unit.lane))
                .map(|(index, _)| index);
            if let Some(target_index) = target_index {
                let target = &mut defenders[target_index];
                let damage = (attacker.attack - target.armor).max(1);
                target.hp = (target.hp - damage).max(0);
                attacker.cooldown_left = attacker.attack_cooldown;
            }
        }
    }

    fn random_index(&mut self, upper: usize) -> usize {
        self.rng_state ^= self.rng_state >> 12;
        self.rng_state ^= self.rng_state << 25;
        self.rng_state ^= self.rng_state >> 27;
        let value = self.rng_state.wrapping_mul(0x2545_F491_4F6C_DD1D);
        (value as usize) % upper
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
    fn draw_consumes_essence_and_adds_recruits_from_lines() {
        let mut run = RunState::new(7);
        let start = run.essence;
        let result = run.draw().unwrap();
        assert_eq!(run.essence, result.essence_left);
        assert!(run.essence <= start);
        assert!(run.party.len() <= PARTY_LIMIT);
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
        RunState::advance_side(&mut attackers, &mut defenders);

        assert_eq!(defenders[0].hp, 20);
        assert_eq!(defenders[1].hp, 15);
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
