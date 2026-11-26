use serde::{Deserialize, Serialize};
use thiserror::Error;

pub const BOARD_SIZE: usize = 3;
pub const LINES: [[(usize, usize); 3]; 8] = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
];

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub enum UnitClass {
    Guardian,
    Archer,
    Mage,
    Cleric,
    Rogue,
    Beast,
}

impl UnitClass {
    pub fn label(self) -> &'static str {
        match self {
            Self::Guardian => "Guardian",
            Self::Archer => "Archer",
            Self::Mage => "Mage",
            Self::Cleric => "Cleric",
            Self::Rogue => "Rogue",
            Self::Beast => "Beast",
        }
    }
    pub fn symbol(self) -> &'static str {
        match self {
            Self::Guardian => "🛡️",
            Self::Archer => "🏹",
            Self::Mage => "🔮",
            Self::Cleric => "✨",
            Self::Rogue => "🗡️",
            Self::Beast => "🐺",
        }
    }
    fn base_stats(self) -> (u32, u32) {
        match self {
            Self::Guardian => (5, 23),
            Self::Archer => (10, 10),
            Self::Mage => (12, 9),
            Self::Cleric => (6, 18),
            Self::Rogue => (9, 12),
            Self::Beast => (8, 17),
        }
    }
    fn imprint(self) -> &'static str {
        match self {
            Self::Guardian => "Fortify",
            Self::Archer => "Pierce",
            Self::Mage => "Spellpower",
            Self::Cleric => "Mending",
            Self::Rogue => "Critical",
            Self::Beast => "Fury",
        }
    }
    fn promotions(self) -> [&'static str; 2] {
        match self {
            Self::Guardian => ["Warden", "Bulwark"],
            Self::Archer => ["Crossbowman", "Pathfinder"],
            Self::Mage => ["Stormcaller", "Arcanist"],
            Self::Cleric => ["Templar", "Oracle"],
            Self::Rogue => ["Duelist", "Trickster"],
            Self::Beast => ["Ravager", "Dire Beast"],
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunPhase {
    Preparation,
    Intermission,
    Lost,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Unit {
    pub id: u64,
    pub class: UnitClass,
    pub level: u16,
    pub absorb_level: u16,
    pub attack: u32,
    pub health: u32,
    pub imprint: Option<String>,
    pub promotion: Option<String>,
    pub pending_promotion: bool,
    pub promotion_options: [String; 2],
    pub locked: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct LineWin {
    pub line: usize,
    pub class: UnitClass,
    pub unit_id: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct SpinReport {
    pub cost: u32,
    pub board: [[UnitClass; BOARD_SIZE]; BOARD_SIZE],
    pub wins: Vec<LineWin>,
    pub jackpot: bool,
    pub gold_awarded: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct BattleReport {
    pub wave: u32,
    pub boss: bool,
    pub army_power: u32,
    pub enemy_power: u32,
    pub victory: bool,
    pub damage_taken: u32,
    pub gold_awarded: u32,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CoreKind {
    Fortune,
    Might,
    Command,
}

impl CoreKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::Fortune => "Fortune Core",
            Self::Might => "Might Core",
            Self::Command => "Command Core",
        }
    }
    pub fn effect(self) -> &'static str {
        match self {
            Self::Fortune => "+15% battle gold",
            Self::Might => "+12% army power",
            Self::Command => "+1 unit capacity",
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ItemKind {
    SharpeningStone,
    VitalityCharm,
    HealingPotion,
}

impl ItemKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::SharpeningStone => "Sharpening Stone",
            Self::VitalityCharm => "Vitality Charm",
            Self::HealingPotion => "Healing Potion",
        }
    }
    pub fn cost(self) -> u32 {
        match self {
            Self::SharpeningStone => 100,
            Self::VitalityCharm => 100,
            Self::HealingPotion => 75,
        }
    }
}

pub fn item_prices() -> [u32; 3] {
    [
        ItemKind::SharpeningStone.cost(),
        ItemKind::VitalityCharm.cost(),
        ItemKind::HealingPotion.cost(),
    ]
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct GameState {
    pub run_id: String,
    pub seed: u64,
    pub wave: u32,
    pub phase: RunPhase,
    pub gold: u32,
    pub hearts: u8,
    pub unit_limit: usize,
    pub spins_remaining: u8,
    pub spins_used: u8,
    pub next_spin_cost: u32,
    pub shop_prices: [u32; 3],
    pub ruleset_version: u32,
    pub nudge_available: bool,
    pub board: [[UnitClass; BOARD_SIZE]; BOARD_SIZE],
    pub units: Vec<Unit>,
    pub cores: Vec<CoreKind>,
    pub items: Vec<ItemKind>,
    pub last_spin: Option<SpinReport>,
    pub last_battle: Option<BattleReport>,
    pub core_offer: Option<[CoreKind; 3]>,
    next_unit_id: u64,
    rng_state: u64,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum GameError {
    #[error("the run has ended")]
    RunEnded,
    #[error("this action is not available during this phase")]
    WrongPhase,
    #[error("no spins remain")]
    NoSpins,
    #[error("not enough gold")]
    NotEnoughGold,
    #[error("unit capacity reached; absorb a unit before spinning again")]
    UnitCapacityReached,
    #[error("invalid column or direction")]
    InvalidNudge,
    #[error("nudging has already been used this wave")]
    NudgeSpent,
    #[error("unit does not exist")]
    UnitNotFound,
    #[error("a unit cannot absorb itself")]
    SameUnit,
    #[error("the target unit is locked")]
    TargetLocked,
    #[error("the donor unit is locked")]
    DonorLocked,
    #[error("promotion choice is not valid for this unit")]
    InvalidPromotion,
    #[error("core offer is not available or the selected index is invalid")]
    InvalidCoreChoice,
    #[error("choose an offered Core before starting the next wave")]
    CoreChoiceRequired,
    #[error("item is not available or the selected item is invalid")]
    InvalidItem,
}

impl GameState {
    pub fn new(seed: u64, run_id: impl Into<String>) -> Self {
        let mut state = Self {
            run_id: run_id.into(),
            seed,
            wave: 1,
            phase: RunPhase::Preparation,
            gold: 500,
            hearts: 5,
            unit_limit: 5,
            spins_remaining: 6,
            spins_used: 0,
            next_spin_cost: 100,
            shop_prices: item_prices(),
            ruleset_version: 1,
            nudge_available: true,
            board: [[UnitClass::Guardian; 3]; 3],
            units: Vec::new(),
            cores: Vec::new(),
            items: Vec::new(),
            last_spin: None,
            last_battle: None,
            core_offer: None,
            next_unit_id: 1,
            rng_state: if seed == 0 {
                0x9E37_79B9_7F4A_7C15
            } else {
                seed
            },
        };
        let starter = state.spawn_unit(UnitClass::Guardian);
        state.units.push(starter);
        state
    }

    pub fn spin_cost(&self) -> u32 {
        100 + u32::from(self.spins_used) * 50
    }

    pub fn spin(&mut self) -> Result<SpinReport, GameError> {
        self.ensure_preparation()?;
        if self.units.len() > self.unit_limit {
            return Err(GameError::UnitCapacityReached);
        }
        if self.spins_remaining == 0 {
            return Err(GameError::NoSpins);
        }
        let cost = self.spin_cost();
        if self.gold < cost {
            return Err(GameError::NotEnoughGold);
        }
        self.gold -= cost;
        self.spins_remaining -= 1;
        self.spins_used = self.spins_used.saturating_add(1);
        self.next_spin_cost = self.spin_cost();
        let mut board = [[UnitClass::Guardian; 3]; 3];
        for row in &mut board {
            for cell in row {
                *cell = self.random_class();
            }
        }
        self.board = board;
        let wins = self.resolve_lines();
        let jackpot = is_jackpot(&board);
        let gold_awarded = if jackpot {
            160
        } else {
            (wins.len() as u32) * 12
        };
        self.gold = self.gold.saturating_add(gold_awarded);
        let report = SpinReport {
            cost,
            board,
            wins,
            jackpot,
            gold_awarded,
        };
        self.last_spin = Some(report.clone());
        Ok(report)
    }

    pub fn nudge(&mut self, column: usize, direction: i8) -> Result<SpinReport, GameError> {
        self.ensure_preparation()?;
        if !self.nudge_available {
            return Err(GameError::NudgeSpent);
        }
        if column >= BOARD_SIZE || ![-1, 1].contains(&direction) {
            return Err(GameError::InvalidNudge);
        }
        let before = self.last_spin.clone().ok_or(GameError::InvalidNudge)?;
        let old_wins: Vec<(usize, UnitClass)> =
            before.wins.iter().map(|w| (w.line, w.class)).collect();
        let shift = if direction < 0 { 1 } else { 2 };
        let old = [
            self.board[0][column],
            self.board[1][column],
            self.board[2][column],
        ];
        for row in 0..BOARD_SIZE {
            self.board[row][column] = old[(row + shift) % BOARD_SIZE];
        }
        let all_wins = self.matching_lines();
        let mut new_wins = Vec::new();
        for (line, class) in all_wins {
            if !old_wins.contains(&(line, class)) {
                let unit = self.spawn_unit(class);
                new_wins.push(LineWin {
                    line,
                    class,
                    unit_id: unit.id,
                });
                self.units.push(unit);
            }
        }
        self.nudge_available = false;
        let mut report = before;
        report.board = self.board;
        report.wins.extend(new_wins);
        self.last_spin = Some(report.clone());
        Ok(report)
    }

    pub fn absorb(&mut self, target_id: u64, donor_id: u64) -> Result<(), GameError> {
        self.ensure_management_phase()?;
        if target_id == donor_id {
            return Err(GameError::SameUnit);
        }
        let target_index = self
            .units
            .iter()
            .position(|u| u.id == target_id)
            .ok_or(GameError::UnitNotFound)?;
        let donor_index = self
            .units
            .iter()
            .position(|u| u.id == donor_id)
            .ok_or(GameError::UnitNotFound)?;
        if self.units[target_index].locked {
            return Err(GameError::TargetLocked);
        }
        if self.units[donor_index].locked {
            return Err(GameError::DonorLocked);
        }
        let donor = self.units.remove(donor_index);
        let target_index = self
            .units
            .iter()
            .position(|u| u.id == target_id)
            .ok_or(GameError::UnitNotFound)?;
        let target = &mut self.units[target_index];
        target.absorb_level = target.absorb_level.saturating_add(1);
        target.level = target.level.saturating_add(1);
        target.attack = target.attack.saturating_add((donor.attack / 5).max(1));
        target.health = target.health.saturating_add((donor.health / 6).max(1));
        if target.imprint.is_none() {
            target.imprint = Some(donor.class.imprint().to_string());
        }
        if target.absorb_level == 5 || target.absorb_level == 12 {
            target.pending_promotion = true;
        }
        Ok(())
    }

    pub fn choose_promotion(&mut self, unit_id: u64, choice: &str) -> Result<(), GameError> {
        self.ensure_management_phase()?;
        let unit = self
            .units
            .iter_mut()
            .find(|u| u.id == unit_id)
            .ok_or(GameError::UnitNotFound)?;
        if !unit.pending_promotion || !unit.class.promotions().contains(&choice) {
            return Err(GameError::InvalidPromotion);
        }
        unit.promotion = Some(choice.to_string());
        unit.pending_promotion = false;
        if choice.contains("Warden") || choice.contains("Bulwark") || choice.contains("Templar") {
            unit.health = unit.health.saturating_add(8);
        } else {
            unit.attack = unit.attack.saturating_add(4);
        }
        Ok(())
    }

    pub fn toggle_lock(&mut self, unit_id: u64) -> Result<(), GameError> {
        self.ensure_management_phase()?;
        let unit = self
            .units
            .iter_mut()
            .find(|u| u.id == unit_id)
            .ok_or(GameError::UnitNotFound)?;
        unit.locked = !unit.locked;
        Ok(())
    }

    pub fn battle(&mut self) -> Result<BattleReport, GameError> {
        self.ensure_preparation()?;
        let boss = self.wave % 5 == 0;
        let army_base = self.units.iter().fold(0u32, |total, unit| {
            let unit_power = unit
                .attack
                .saturating_add(unit.health / 4)
                .saturating_add(u32::from(unit.level).saturating_mul(2));
            total.saturating_add(unit_power)
        });
        let item_bonus = self
            .items
            .iter()
            .filter(|i| **i == ItemKind::SharpeningStone)
            .count() as u32
            * 3;
        let core_percent =
            100 + self.cores.iter().filter(|c| **c == CoreKind::Might).count() as u32 * 12;
        let class_synergy = self
            .units
            .iter()
            .fold([0u8; 6], |mut counts, unit| {
                let index = match unit.class {
                    UnitClass::Guardian => 0,
                    UnitClass::Archer => 1,
                    UnitClass::Mage => 2,
                    UnitClass::Cleric => 3,
                    UnitClass::Rogue => 4,
                    UnitClass::Beast => 5,
                };
                counts[index] = counts[index].saturating_add(1);
                counts
            })
            .iter()
            .any(|count| *count >= 3);
        let synergy_percent = if class_synergy { 110 } else { 100 };
        let army_power = army_base
            .saturating_add(item_bonus)
            .saturating_mul(core_percent)
            .saturating_mul(synergy_percent)
            / 10_000;
        let mut enemy_power = 24u32.saturating_add(self.wave.saturating_mul(13));
        if boss {
            enemy_power = enemy_power.saturating_mul(3) / 2;
        }
        let victory = army_power >= enemy_power;
        let raw_damage = if victory {
            0
        } else {
            (1 + (enemy_power - army_power) / 28).min(3)
        };
        let has_vitality = self.items.contains(&ItemKind::VitalityCharm);
        let damage_taken = if has_vitality && raw_damage > 0 {
            raw_damage.saturating_sub(1)
        } else {
            raw_damage
        };
        self.hearts = self.hearts.saturating_sub(damage_taken as u8);
        let mut gold_awarded = if victory {
            35u32
                .saturating_add(self.wave.saturating_mul(9))
                .saturating_add(if boss { 50 } else { 0 })
        } else {
            10
        };
        let fortune = self
            .cores
            .iter()
            .filter(|c| **c == CoreKind::Fortune)
            .count() as u32;
        gold_awarded = gold_awarded.saturating_mul(100 + fortune * 15) / 100;
        self.gold = self.gold.saturating_add(gold_awarded);
        if boss && victory && self.cores.len() < 8 {
            self.core_offer = Some([CoreKind::Fortune, CoreKind::Might, CoreKind::Command]);
        }
        if self.hearts == 0 {
            self.phase = RunPhase::Lost;
        } else {
            self.phase = RunPhase::Intermission;
        }
        let report = BattleReport {
            wave: self.wave,
            boss,
            army_power,
            enemy_power,
            victory,
            damage_taken,
            gold_awarded,
        };
        self.last_battle = Some(report.clone());
        Ok(report)
    }

    pub fn choose_core(&mut self, index: usize) -> Result<(), GameError> {
        if self.phase != RunPhase::Intermission {
            return Err(GameError::WrongPhase);
        }
        if self.cores.len() >= 8 {
            return Err(GameError::InvalidCoreChoice);
        }
        let offers = self.core_offer.ok_or(GameError::InvalidCoreChoice)?;
        let chosen = *offers.get(index).ok_or(GameError::InvalidCoreChoice)?;
        self.core_offer = None;
        self.cores.push(chosen);
        if chosen == CoreKind::Command {
            self.unit_limit = self.unit_limit.saturating_add(1);
        }
        Ok(())
    }

    pub fn buy_item(&mut self, item: ItemKind) -> Result<(), GameError> {
        if self.phase != RunPhase::Intermission {
            return Err(GameError::WrongPhase);
        }
        let cost = item.cost();
        if self.gold < cost {
            return Err(GameError::NotEnoughGold);
        }
        if item == ItemKind::HealingPotion && self.hearts >= 5 {
            return Err(GameError::InvalidItem);
        }
        self.gold -= cost;
        match item {
            ItemKind::HealingPotion => {
                self.hearts = (self.hearts + 1).min(5);
            }
            other => self.items.push(other),
        }
        Ok(())
    }

    pub fn next_wave(&mut self) -> Result<(), GameError> {
        if self.phase != RunPhase::Intermission {
            return Err(GameError::WrongPhase);
        }
        if self.core_offer.is_some() {
            return Err(GameError::CoreChoiceRequired);
        }
        self.wave = self.wave.saturating_add(1);
        self.spins_remaining = 6;
        self.spins_used = 0;
        self.next_spin_cost = 100;
        self.nudge_available = true;
        self.last_spin = None;
        self.last_battle = None;
        self.phase = RunPhase::Preparation;
        Ok(())
    }

    fn ensure_preparation(&self) -> Result<(), GameError> {
        if self.phase == RunPhase::Lost {
            Err(GameError::RunEnded)
        } else if self.phase != RunPhase::Preparation {
            Err(GameError::WrongPhase)
        } else {
            Ok(())
        }
    }

    fn ensure_management_phase(&self) -> Result<(), GameError> {
        if self.phase == RunPhase::Lost {
            return Err(GameError::RunEnded);
        }
        if matches!(self.phase, RunPhase::Preparation | RunPhase::Intermission) {
            Ok(())
        } else {
            Err(GameError::WrongPhase)
        }
    }

    fn spawn_unit(&mut self, class: UnitClass) -> Unit {
        let id = self.next_unit_id;
        self.next_unit_id = self.next_unit_id.saturating_add(1);
        let (attack, health) = class.base_stats();
        let variance = self.random_u32() % 3;
        let options = class.promotions();
        Unit {
            id,
            class,
            level: 1,
            absorb_level: 0,
            attack: attack + variance,
            health: health + variance,
            imprint: None,
            promotion: None,
            pending_promotion: false,
            promotion_options: [options[0].to_string(), options[1].to_string()],
            locked: false,
        }
    }

    fn matching_lines(&self) -> Vec<(usize, UnitClass)> {
        LINES
            .iter()
            .enumerate()
            .filter_map(|(i, line)| {
                let first = self.board[line[0].0][line[0].1];
                let same = line.iter().all(|(r, c)| self.board[*r][*c] == first);
                same.then_some((i, first))
            })
            .collect()
    }

    fn resolve_lines(&mut self) -> Vec<LineWin> {
        let matches = self.matching_lines();
        let mut wins = Vec::with_capacity(matches.len());
        for (line, class) in matches {
            let unit = self.spawn_unit(class);
            wins.push(LineWin {
                line,
                class,
                unit_id: unit.id,
            });
            self.units.push(unit);
        }
        wins
    }

    fn random_class(&mut self) -> UnitClass {
        match self.random_u32() % 6 {
            0 => UnitClass::Guardian,
            1 => UnitClass::Archer,
            2 => UnitClass::Mage,
            3 => UnitClass::Cleric,
            4 => UnitClass::Rogue,
            _ => UnitClass::Beast,
        }
    }

    fn random_u32(&mut self) -> u32 {
        let mut x = self.rng_state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.rng_state = x;
        (x >> 16) as u32
    }
}

fn is_jackpot(board: &[[UnitClass; BOARD_SIZE]; BOARD_SIZE]) -> bool {
    board.iter().flatten().all(|class| *class == board[0][0])
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run(seed: u64) -> GameState {
        GameState::new(seed, "test-run")
    }

    #[test]
    fn board_has_eight_paylines() {
        assert_eq!(LINES.len(), 8);
    }

    #[test]
    fn same_seed_repeats_spin_board() {
        let mut a = run(42);
        let mut b = run(42);
        assert_eq!(a.spin().unwrap().board, b.spin().unwrap().board);
    }

    #[test]
    fn spin_consumes_incremental_gold_and_spin_count() {
        let mut game = run(7);
        let first = game.spin().unwrap();
        assert_eq!(first.cost, 100);
        assert_eq!(game.gold, 400 + first.gold_awarded);
        assert_eq!(game.spins_remaining, 5);
        assert_eq!(game.spin_cost(), 150);
        assert_eq!(game.next_spin_cost, 150);
    }

    #[test]
    fn all_nine_equal_is_jackpot_and_pays_all_lines() {
        let mut game = run(9);
        game.board = [[UnitClass::Mage; 3]; 3];
        assert!(is_jackpot(&game.board));
        let wins = game.resolve_lines();
        assert_eq!(wins.len(), 8);
        assert_eq!(game.units.len(), 9);
    }

    #[test]
    fn cannot_spin_when_army_is_over_capacity() {
        let mut game = run(11);
        game.unit_limit = 0;
        assert_eq!(game.spin(), Err(GameError::UnitCapacityReached));
    }

    #[test]
    fn nudge_is_once_per_wave_and_checks_bounds() {
        let mut game = run(15);
        game.spin().unwrap();
        assert!(game.nudge(3, 1).is_err());
        game.nudge(1, 1).unwrap();
        assert_eq!(game.nudge(1, -1), Err(GameError::NudgeSpent));
    }

    #[test]
    fn absorb_consumes_donor_and_levels_target() {
        let mut game = run(20);
        let target = game.units[0].id;
        let donor = game.spawn_unit(UnitClass::Archer);
        let donor_id = donor.id;
        game.units.push(donor);
        let count = game.units.len();
        game.absorb(target, donor_id).unwrap();
        assert_eq!(game.units.len(), count - 1);
        let upgraded = game.units.iter().find(|u| u.id == target).unwrap();
        assert_eq!(upgraded.absorb_level, 1);
        assert!(upgraded.imprint.is_some());
    }

    #[test]
    fn absorb_rejects_self_and_locked_donor() {
        let mut game = run(21);
        let id = game.units[0].id;
        assert_eq!(game.absorb(id, id), Err(GameError::SameUnit));
        let donor = game.spawn_unit(UnitClass::Rogue);
        let donor_id = donor.id;
        game.units.push(donor);
        game.units.last_mut().unwrap().locked = true;
        assert_eq!(game.absorb(id, donor_id), Err(GameError::DonorLocked));
    }

    #[test]
    fn promotion_is_required_at_threshold_and_choice_is_validated() {
        let mut game = run(22);
        let target = game.units[0].id;
        for _ in 0..5 {
            let donor = game.spawn_unit(UnitClass::Archer);
            let id = donor.id;
            game.units.push(donor);
            game.absorb(target, id).unwrap();
        }
        let unit = game.units.iter().find(|u| u.id == target).unwrap();
        assert!(unit.pending_promotion);
        assert_eq!(
            game.choose_promotion(target, "not-a-class"),
            Err(GameError::InvalidPromotion)
        );
        game.choose_promotion(target, "Warden").unwrap();
        assert!(
            !game
                .units
                .iter()
                .find(|u| u.id == target)
                .unwrap()
                .pending_promotion
        );
    }

    #[test]
    fn battle_and_next_wave_follow_state_machine() {
        let mut game = run(23);
        let report = game.battle().unwrap();
        assert_eq!(report.wave, 1);
        assert_eq!(game.phase, RunPhase::Intermission);
        game.next_wave().unwrap();
        assert_eq!(game.wave, 2);
        assert_eq!(game.spins_remaining, 6);
        assert_eq!(game.phase, RunPhase::Preparation);
        assert_eq!(game.next_spin_cost, 100);
    }

    #[test]
    fn boss_wave_offers_core_when_won() {
        let mut game = run(24);
        game.wave = 5;
        for _ in 0..4 {
            let donor = game.spawn_unit(UnitClass::Mage);
            game.units.push(donor);
        }
        game.units.iter_mut().for_each(|u| {
            u.attack = 100;
            u.health = 100;
        });
        let report = game.battle().unwrap();
        assert!(report.boss);
        assert!(report.victory);
        assert!(game.core_offer.is_some());
        game.choose_core(2).unwrap();
        assert_eq!(game.unit_limit, 6);
    }

    #[test]
    fn shop_checks_gold_and_applies_healing() {
        let mut game = run(25);
        game.phase = RunPhase::Intermission;
        game.hearts = 3;
        game.buy_item(ItemKind::HealingPotion).unwrap();
        assert_eq!(game.hearts, 4);
        assert_eq!(game.gold, 425);
    }

    #[test]
    fn absorption_is_available_between_waves() {
        let mut game = run(27);
        game.phase = RunPhase::Intermission;
        let target = game.units[0].id;
        let donor = game.spawn_unit(UnitClass::Rogue);
        let donor_id = donor.id;
        game.units.push(donor);
        assert!(game.absorb(target, donor_id).is_ok());
    }

    #[test]
    fn invalid_core_selection_does_not_consume_offer() {
        let mut game = run(28);
        game.phase = RunPhase::Intermission;
        game.core_offer = Some([CoreKind::Fortune, CoreKind::Might, CoreKind::Command]);
        assert_eq!(game.choose_core(9), Err(GameError::InvalidCoreChoice));
        assert!(game.core_offer.is_some());
    }

    #[test]
    fn lost_run_rejects_future_spins() {
        let mut game = run(26);
        game.hearts = 1;
        game.units.clear();
        game.battle().unwrap();
        assert_eq!(game.phase, RunPhase::Lost);
        assert_eq!(game.spin(), Err(GameError::RunEnded));
    }

    #[test]
    fn boss_core_offer_must_be_resolved_before_next_wave() {
        let mut game = run(29);
        game.wave = 5;
        for _ in 0..4 {
            let donor = game.spawn_unit(UnitClass::Mage);
            game.units.push(donor);
        }
        game.units.iter_mut().for_each(|u| {
            u.attack = 100;
            u.health = 100;
        });
        game.battle().unwrap();
        assert_eq!(game.next_wave(), Err(GameError::CoreChoiceRequired));
        game.choose_core(0).unwrap();
        assert!(game.next_wave().is_ok());
    }
}
