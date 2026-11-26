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
    #[serde(default)]
    pub current_health: Option<u32>,
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
    #[serde(default)]
    pub rounds: u32,
    #[serde(default)]
    pub events: Vec<BattleEvent>,
    #[serde(default)]
    pub route: Option<RouteNodeKind>,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BattleEventKind {
    AllyAttack,
    EnemyAttack,
    AllyDefeated,
    EnemyDefeated,
    UnitHealed,
    BossTelegraph,
    BattleEnded,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct BattleEvent {
    pub tick: u32,
    pub kind: BattleEventKind,
    pub actor_id: u64,
    pub target_id: u64,
    pub actor: String,
    pub target: String,
    pub amount: u32,
    pub remaining_health: u32,
}

#[derive(Clone, Debug)]
struct Combatant {
    id: u64,
    name: String,
    class: Option<UnitClass>,
    attack: u32,
    max_health: u32,
    current_health: u32,
    initiative: u8,
    boss: bool,
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

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum JourneyEventKind {
    LostCache,
    MoonwellShrine,
    TravellingMerchant,
    WoundedRanger,
    BanditAmbush,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct JourneyChoice {
    pub label: String,
    pub description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct JourneyEvent {
    pub id: String,
    pub wave: u32,
    pub kind: JourneyEventKind,
    pub title: String,
    pub description: String,
    pub choices: Vec<JourneyChoice>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct JourneyEventResolution {
    pub event_id: String,
    pub choice_index: usize,
    pub outcome: String,
}


#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RouteNodeKind {
    Battle,
    Rest,
    Merchant,
    Elite,
    BossGate,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RouteOption {
    pub id: String,
    pub kind: RouteNodeKind,
    pub title: String,
    pub description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RouteResolution {
    pub wave: u32,
    pub kind: RouteNodeKind,
    pub outcome: String,
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
    #[serde(default)]
    pub pending_event: Option<JourneyEvent>,
    #[serde(default)]
    pub event_history: Vec<JourneyEventResolution>,
    #[serde(default)]
    pub pending_route: Option<Vec<RouteOption>>,
    #[serde(default)]
    pub current_route: Option<RouteNodeKind>,
    #[serde(default)]
    pub route_history: Vec<RouteResolution>,
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
    #[error("resolve the journey event before starting the next wave")]
    JourneyEventRequired,
    #[error("there is no pending journey event")]
    NoJourneyEvent,
    #[error("journey event choice is invalid")]
    InvalidJourneyChoice,
    #[error("choose a route before starting the next wave")]
    JourneyRouteRequired,
    #[error("there is no pending route choice")]
    NoJourneyRoute,
    #[error("route choice is invalid for this expedition stage")]
    InvalidRouteChoice,
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
            pending_event: None,
            event_history: Vec::new(),
            pending_route: None,
            current_route: None,
            route_history: Vec::new(),
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
        let health_bonus = (donor.health / 6).max(1);
        target.health = target.health.saturating_add(health_bonus);
        if let Some(current) = target.current_health.as_mut() {
            *current = current.saturating_add(health_bonus).min(target.health);
        }
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
            if let Some(current) = unit.current_health.as_mut() {
                *current = current.saturating_add(8).min(unit.health);
            }
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
            .filter(|item| **item == ItemKind::SharpeningStone)
            .count() as u32
            * 3;
        let core_percent = 100
            + self
                .cores
                .iter()
                .filter(|core| **core == CoreKind::Might)
                .count() as u32
                * 12;
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

        let mut allies: Vec<Combatant> = self
            .units
            .iter()
            .map(|unit| Combatant {
                id: unit.id,
                name: format!("{} #{}", unit.class.label(), unit.id),
                class: Some(unit.class),
                attack: unit.attack,
                max_health: unit.health.max(1),
                current_health: unit
                    .current_health
                    .unwrap_or(unit.health)
                    .min(unit.health)
                    .max(1),
                initiative: match unit.class {
                    UnitClass::Rogue => 10,
                    UnitClass::Archer => 9,
                    UnitClass::Mage => 8,
                    UnitClass::Beast => 7,
                    UnitClass::Guardian => 6,
                    UnitClass::Cleric => 5,
                },
                boss: false,
            })
            .collect();
        let route = self.current_route;
        let elite = route == Some(RouteNodeKind::Elite) && !boss;
        let mut enemies = build_enemy_party(self.wave, boss, elite);
        let enemy_power = enemies.iter().fold(0u32, |total, enemy| {
            total
                .saturating_add(enemy.attack)
                .saturating_add(enemy.max_health / 4)
        });
        let mut events = Vec::new();
        let mut rounds = 0u32;

        for tick in 1..=40 {
            if allies.is_empty() || enemies.is_empty() {
                break;
            }
            rounds = tick;
            allies.sort_by_key(|unit| (std::cmp::Reverse(unit.initiative), unit.id));

            for actor_index in 0..allies.len() {
                if allies[actor_index].current_health == 0 || enemies.is_empty() {
                    continue;
                }
                let actor = allies[actor_index].clone();
                let target_index = enemies
                    .iter()
                    .enumerate()
                    .min_by_key(|(_, enemy)| {
                        (
                            enemy.current_health.saturating_mul(100) / enemy.max_health.max(1),
                            enemy.id,
                        )
                    })
                    .map(|(index, _)| index)
                    .expect("enemy list is checked as non-empty");
                let target = enemies[target_index].clone();
                let class_bonus = match actor.class {
                    Some(UnitClass::Rogue) => 2,
                    Some(UnitClass::Archer) if tick % 2 == 0 => 2,
                    Some(UnitClass::Beast)
                        if target.current_health.saturating_mul(2) > target.max_health =>
                    {
                        1
                    }
                    _ => 0,
                };
                let attack = actor
                    .attack
                    .saturating_add(class_bonus)
                    .saturating_add(item_bonus / 3);
                let damage = attack
                    .saturating_mul(core_percent)
                    .saturating_mul(synergy_percent)
                    / 10_000u32;
                let target_health = &mut enemies[target_index].current_health;
                *target_health = target_health.saturating_sub(damage);
                let remaining = *target_health;
                events.push(BattleEvent {
                    tick,
                    kind: BattleEventKind::AllyAttack,
                    actor_id: actor.id,
                    target_id: target.id,
                    actor: actor.name.clone(),
                    target: target.name.clone(),
                    amount: damage,
                    remaining_health: remaining,
                });
                if remaining == 0 {
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::EnemyDefeated,
                        actor_id: actor.id,
                        target_id: target.id,
                        actor: actor.name.clone(),
                        target: target.name.clone(),
                        amount: 0,
                        remaining_health: 0,
                    });
                    enemies.remove(target_index);
                }

                if actor.class == Some(UnitClass::Mage) && tick % 2 == 0 && !enemies.is_empty() {
                    let splash_index = enemies
                        .iter()
                        .enumerate()
                        .min_by_key(|(_, enemy)| {
                            (
                                enemy.current_health.saturating_mul(100) / enemy.max_health.max(1),
                                enemy.id,
                            )
                        })
                        .map(|(index, _)| index)
                        .expect("enemy list is checked as non-empty");
                    let splash_target = enemies[splash_index].clone();
                    let splash_damage = 2u32.saturating_mul(core_percent) / 100;
                    enemies[splash_index].current_health = enemies[splash_index]
                        .current_health
                        .saturating_sub(splash_damage.max(1));
                    let splash_remaining = enemies[splash_index].current_health;
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::AllyAttack,
                        actor_id: actor.id,
                        target_id: splash_target.id,
                        actor: format!("{} (spell)", actor.name),
                        target: splash_target.name.clone(),
                        amount: splash_damage.max(1),
                        remaining_health: splash_remaining,
                    });
                    if splash_remaining == 0 {
                        events.push(BattleEvent {
                            tick,
                            kind: BattleEventKind::EnemyDefeated,
                            actor_id: actor.id,
                            target_id: splash_target.id,
                            actor: actor.name.clone(),
                            target: splash_target.name,
                            amount: 0,
                            remaining_health: 0,
                        });
                        enemies.remove(splash_index);
                    }
                }

                if actor.class == Some(UnitClass::Cleric) && tick % 2 == 0 {
                    if let Some((ally_index, _)) = allies
                        .iter()
                        .enumerate()
                        .filter(|(_, ally)| {
                            ally.current_health > 0 && ally.current_health < ally.max_health
                        })
                        .min_by_key(|(_, ally)| {
                            (
                                ally.current_health.saturating_mul(100) / ally.max_health.max(1),
                                ally.id,
                            )
                        })
                    {
                        let healed = 2u32
                            .min(allies[ally_index].max_health - allies[ally_index].current_health);
                        allies[ally_index].current_health =
                            allies[ally_index].current_health.saturating_add(healed);
                        events.push(BattleEvent {
                            tick,
                            kind: BattleEventKind::UnitHealed,
                            actor_id: actor.id,
                            target_id: allies[ally_index].id,
                            actor: actor.name.clone(),
                            target: allies[ally_index].name.clone(),
                            amount: healed,
                            remaining_health: allies[ally_index].current_health,
                        });
                    }
                }
            }

            let enemy_turn: Vec<Combatant> = enemies.clone();
            for enemy in enemy_turn {
                if !enemies
                    .iter()
                    .any(|current| current.id == enemy.id && current.current_health > 0)
                {
                    continue;
                }
                if enemy.boss && tick % 3 == 0 {
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::BossTelegraph,
                        actor_id: enemy.id,
                        target_id: 0,
                        actor: enemy.name.clone(),
                        target: "front line".to_string(),
                        amount: 0,
                        remaining_health: 0,
                    });
                }
                let target_index = allies
                    .iter()
                    .enumerate()
                    .filter(|(_, ally)| ally.current_health > 0)
                    .min_by_key(|(_, ally)| {
                        (
                            if ally.class == Some(UnitClass::Guardian) {
                                0u8
                            } else {
                                1u8
                            },
                            ally.current_health.saturating_mul(100) / ally.max_health.max(1),
                            ally.id,
                        )
                    })
                    .map(|(index, _)| index);
                let Some(target_index) = target_index else {
                    break;
                };
                let target = allies[target_index].clone();
                let telegraph_bonus = if enemy.boss && tick % 3 == 0 { 2 } else { 0 };
                let guard_reduction = if target.class == Some(UnitClass::Guardian) {
                    1
                } else {
                    0
                };
                let damage = enemy
                    .attack
                    .saturating_add(telegraph_bonus)
                    .saturating_sub(guard_reduction)
                    .max(1);
                allies[target_index].current_health =
                    allies[target_index].current_health.saturating_sub(damage);
                let remaining = allies[target_index].current_health;
                events.push(BattleEvent {
                    tick,
                    kind: BattleEventKind::EnemyAttack,
                    actor_id: enemy.id,
                    target_id: target.id,
                    actor: enemy.name.clone(),
                    target: target.name.clone(),
                    amount: damage,
                    remaining_health: remaining,
                });
                if remaining == 0 {
                    events.push(BattleEvent {
                        tick,
                        kind: BattleEventKind::AllyDefeated,
                        actor_id: enemy.id,
                        target_id: target.id,
                        actor: enemy.name.clone(),
                        target: target.name,
                        amount: 0,
                        remaining_health: 0,
                    });
                }
            }

            allies.retain(|ally| ally.current_health > 0);
            if allies.is_empty() || enemies.is_empty() {
                break;
            }
        }

        let victory = enemies.is_empty();
        for unit in &mut self.units {
            if let Some(survivor) = allies.iter().find(|ally| ally.id == unit.id) {
                unit.current_health = if survivor.current_health >= unit.health {
                    None
                } else {
                    Some(survivor.current_health)
                };
            } else {
                unit.current_health = Some(0);
            }
        }
        let surviving_ids: Vec<u64> = allies.iter().map(|ally| ally.id).collect();
        self.units.retain(|unit| surviving_ids.contains(&unit.id));

        let raw_damage = if victory {
            0
        } else {
            1 + ((enemies.len() as u32).saturating_sub(1) / 2).min(2)
        };
        let has_vitality = self.items.contains(&ItemKind::VitalityCharm);
        let damage_taken = if has_vitality && raw_damage > 0 {
            raw_damage.saturating_sub(1)
        } else {
            raw_damage
        };
        self.hearts = self
            .hearts
            .saturating_sub(damage_taken.min(u32::from(u8::MAX)) as u8);

        let mut gold_awarded = if victory {
            35u32
                .saturating_add(self.wave.saturating_mul(9))
                .saturating_add(if boss { 50 } else { 0 })
                .saturating_add(if elite { 35 } else { 0 })
        } else {
            10
        };
        let fortune = self
            .cores
            .iter()
            .filter(|core| **core == CoreKind::Fortune)
            .count() as u32;
        gold_awarded = gold_awarded.saturating_mul(100 + fortune * 15) / 100;
        self.gold = self.gold.saturating_add(gold_awarded);
        if boss && victory && self.cores.len() < 8 {
            self.core_offer = Some([CoreKind::Fortune, CoreKind::Might, CoreKind::Command]);
        }
        if self.hearts == 0 {
            self.phase = RunPhase::Lost;
            self.pending_event = None;
        } else {
            self.phase = RunPhase::Intermission;
            let event = self.generate_journey_event();
            self.pending_event = Some(event);
        }
        events.push(BattleEvent {
            tick: rounds,
            kind: BattleEventKind::BattleEnded,
            actor_id: 0,
            target_id: 0,
            actor: "Squad".to_string(),
            target: if victory { "Victory" } else { "Defeat" }.to_string(),
            amount: damage_taken,
            remaining_health: u32::from(self.hearts),
        });
        let report = BattleReport {
            wave: self.wave,
            boss,
            army_power,
            enemy_power,
            victory,
            damage_taken,
            gold_awarded,
            rounds,
            events,
            route,
        };
        self.last_battle = Some(report.clone());
        self.current_route = None;
        Ok(report)
    }

    fn generate_journey_event(&mut self) -> JourneyEvent {
        let roll = self.random_u32() % 100;
        let kind = match roll {
            0..=24 => JourneyEventKind::LostCache,
            25..=44 => JourneyEventKind::MoonwellShrine,
            45..=64 => JourneyEventKind::TravellingMerchant,
            65..=79 => JourneyEventKind::WoundedRanger,
            _ => JourneyEventKind::BanditAmbush,
        };
        let (title, description, choices) = match kind {
            JourneyEventKind::LostCache => (
                "A cache beneath the roots",
                "A moss-covered chest lies half-buried beside the old road. Something valuable remains inside.",
                vec![
                    ("Take the gold", "Gain 70 gold."),
                    ("Drink the tonic", "Restore one heart, up to the run limit."),
                ],
            ),
            JourneyEventKind::MoonwellShrine => (
                "The moonwell shrine",
                "Silver water circles a cracked stone altar. The shrine answers only one offering.",
                vec![
                    (
                        "Offer 60 gold",
                        "Restore up to 4 health to every surviving unit.",
                    ),
                    ("Take the blessing", "Every surviving unit gains 2 attack."),
                ],
            ),
            JourneyEventKind::TravellingMerchant => (
                "A travelling merchant",
                "A lantern-lit cart blocks the narrow forest path. Its owner has one rare supply.",
                vec![
                    (
                        "Buy a sharpening stone · 80 gold",
                        "Gain a permanent battle attack item.",
                    ),
                    ("Trade stories", "Leave peacefully and gain 25 gold."),
                ],
            ),
            JourneyEventKind::WoundedRanger => (
                "A wounded ranger",
                "A scout from the northern trail offers to join, if you can spare supplies.",
                vec![
                    (
                        "Recruit · 50 gold",
                        "Recruit a random class if your formation has room.",
                    ),
                    (
                        "Share provisions",
                        "Gain 35 gold from the ranger's recovered map.",
                    ),
                ],
            ),
            JourneyEventKind::BanditAmbush => (
                "Bandits on the old road",
                "Masked bandits demand payment. You can surrender your purse or fight through.",
                vec![
                    ("Pay the toll", "Lose 40 gold and avoid injury."),
                    ("Stand your ground", "Gain 90 gold, but lose one heart."),
                ],
            ),
        };
        JourneyEvent {
            id: format!("wave-{}-event", self.wave),
            wave: self.wave,
            kind,
            title: title.to_string(),
            description: description.to_string(),
            choices: choices
                .into_iter()
                .map(|(label, description)| JourneyChoice {
                    label: label.to_string(),
                    description: description.to_string(),
                })
                .collect(),
        }
    }

    pub fn resolve_journey_event(&mut self, choice_index: usize) -> Result<(), GameError> {
        if self.phase != RunPhase::Intermission {
            return Err(GameError::WrongPhase);
        }
        let event = self
            .pending_event
            .clone()
            .ok_or(GameError::NoJourneyEvent)?;
        if choice_index >= event.choices.len() {
            return Err(GameError::InvalidJourneyChoice);
        }
        let outcome = match event.kind {
            JourneyEventKind::LostCache => {
                if choice_index == 0 {
                    self.gold = self.gold.saturating_add(70);
                    "Recovered 70 gold.".to_string()
                } else {
                    self.hearts = self.hearts.saturating_add(1).min(5);
                    "The tonic restored one heart.".to_string()
                }
            }
            JourneyEventKind::MoonwellShrine => {
                if choice_index == 0 {
                    if self.gold < 60 {
                        return Err(GameError::NotEnoughGold);
                    }
                    self.gold -= 60;
                    for unit in &mut self.units {
                        unit.current_health = Some(
                            unit.current_health
                                .unwrap_or(unit.health)
                                .saturating_add(4)
                                .min(unit.health),
                        );
                        if unit.current_health == Some(unit.health) {
                            unit.current_health = None;
                        }
                    }
                    "The moonwell restored up to 4 health to every survivor.".to_string()
                } else {
                    for unit in &mut self.units {
                        unit.attack = unit.attack.saturating_add(2);
                    }
                    "The moonwell blessed the army: +2 attack to every survivor.".to_string()
                }
            }
            JourneyEventKind::TravellingMerchant => {
                if choice_index == 0 {
                    if self.gold < 80 {
                        return Err(GameError::NotEnoughGold);
                    }
                    self.gold -= 80;
                    self.items.push(ItemKind::SharpeningStone);
                    "Purchased a sharpening stone.".to_string()
                } else {
                    self.gold = self.gold.saturating_add(25);
                    "The merchant shared a useful map: +25 gold.".to_string()
                }
            }
            JourneyEventKind::WoundedRanger => {
                if choice_index == 0 {
                    if self.gold < 50 {
                        return Err(GameError::NotEnoughGold);
                    }
                    if self.units.len() >= self.unit_limit {
                        return Err(GameError::UnitCapacityReached);
                    }
                    self.gold -= 50;
                    let class = self.random_class();
                    let recruit = self.spawn_unit(class);
                    self.units.push(recruit);
                    format!("A {:?} ranger joined the formation.", class)
                } else {
                    self.gold = self.gold.saturating_add(35);
                    "The ranger shared a recovered map: +35 gold.".to_string()
                }
            }
            JourneyEventKind::BanditAmbush => {
                if choice_index == 0 {
                    if self.gold < 40 {
                        return Err(GameError::NotEnoughGold);
                    }
                    self.gold -= 40;
                    "Paid the toll. The army escaped without injury.".to_string()
                } else {
                    self.gold = self.gold.saturating_add(90);
                    self.hearts = self.hearts.saturating_sub(1);
                    if self.hearts == 0 {
                        self.phase = RunPhase::Lost;
                    }
                    "The bandits fled. Recovered 90 gold, but lost one heart.".to_string()
                }
            }
        };

        self.event_history.push(JourneyEventResolution {
            event_id: event.id,
            choice_index,
            outcome,
        });
        self.pending_event = None;
        if self.phase == RunPhase::Intermission {
            self.pending_route = Some(self.generate_route_options(self.wave.saturating_add(1)));
        } else {
            self.pending_route = None;
        }
        Ok(())
    }

    fn generate_route_options(&mut self, target_wave: u32) -> Vec<RouteOption> {
        let kinds = if target_wave % 5 == 0 {
            [RouteNodeKind::Rest, RouteNodeKind::Merchant, RouteNodeKind::BossGate, RouteNodeKind::BossGate]
        } else {
            [RouteNodeKind::Battle, RouteNodeKind::Rest, RouteNodeKind::Merchant, RouteNodeKind::Elite]
        };
        let start = (self.random_u32() % 4) as usize;
        let mut selected = Vec::with_capacity(3);
        for offset in 0..4 {
            let kind = kinds[(start + offset) % 4];
            if selected.iter().any(|option: &RouteOption| option.kind == kind) {
                continue;
            }
            let (title, description) = match kind {
                RouteNodeKind::Battle => ("Old forest road", "A standard encounter. No detours, no extra danger."),
                RouteNodeKind::Rest => ("Mosslight sanctuary", "Recover one heart and restore 5 health to each surviving companion."),
                RouteNodeKind::Merchant => ("Caravan crossing", "Find a travelling supply cart and gain 75 gold for the expedition."),
                RouteNodeKind::Elite => ("Thornwarden lair", "Face an elite enemy group. The route pays an extra 35 gold if you win."),
                RouteNodeKind::BossGate => ("Ancient boss gate", "The next wave is a boss encounter. Choose your approach before entering."),
            };
            selected.push(RouteOption {
                id: format!("route-{target_wave}-{}", match kind {
                    RouteNodeKind::Battle => "battle",
                    RouteNodeKind::Rest => "rest",
                    RouteNodeKind::Merchant => "merchant",
                    RouteNodeKind::Elite => "elite",
                    RouteNodeKind::BossGate => "boss",
                }),
                kind,
                title: title.to_string(),
                description: description.to_string(),
            });
            if selected.len() == 3 { break; }
        }
        selected
    }

    pub fn choose_route(&mut self, index: usize) -> Result<(), GameError> {
        if self.phase != RunPhase::Intermission {
            return Err(GameError::WrongPhase);
        }
        if self.pending_event.is_some() {
            return Err(GameError::JourneyEventRequired);
        }
        let options = self.pending_route.clone().ok_or(GameError::NoJourneyRoute)?;
        let option = options.get(index).cloned().ok_or(GameError::InvalidRouteChoice)?;
        let target_wave = self.wave.saturating_add(1);
        if option.kind == RouteNodeKind::BossGate && target_wave % 5 != 0 {
            return Err(GameError::InvalidRouteChoice);
        }
        let outcome = match option.kind {
            RouteNodeKind::Battle => "Entered the standard forest route.".to_string(),
            RouteNodeKind::Rest => {
                self.hearts = self.hearts.saturating_add(1).min(5);
                for unit in &mut self.units {
                    let health = unit.current_health.unwrap_or(unit.health);
                    let restored = health.saturating_add(5).min(unit.health);
                    unit.current_health = (restored < unit.health).then_some(restored);
                }
                "Rested at Mosslight sanctuary: +1 heart and up to 5 health per survivor.".to_string()
            }
            RouteNodeKind::Merchant => {
                self.gold = self.gold.saturating_add(75);
                "Traded at the caravan crossing: +75 gold.".to_string()
            }
            RouteNodeKind::Elite => "Entered Thornwarden lair: elite enemies ahead, +35 gold on victory.".to_string(),
            RouteNodeKind::BossGate => "Entered the ancient boss gate.".to_string(),
        };
        self.route_history.push(RouteResolution {
            wave: target_wave,
            kind: option.kind,
            outcome,
        });
        self.current_route = Some(option.kind);
        self.pending_route = None;
        Ok(())
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
        if self.pending_event.is_some() {
            return Err(GameError::JourneyEventRequired);
        }
        if self.pending_route.is_some() || self.current_route.is_none() {
            return Err(GameError::JourneyRouteRequired);
        }
        self.wave = self.wave.saturating_add(1);
        self.spins_remaining = 6;
        self.spins_used = 0;
        self.next_spin_cost = 100;
        self.nudge_available = true;
        self.last_spin = None;
        self.last_battle = None;
        self.pending_event = None;
        for unit in &mut self.units {
            let restored = unit
                .current_health
                .map(|current| current.saturating_add(2).min(unit.health));
            unit.current_health = restored.filter(|current| *current < unit.health);
        }
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
            current_health: None,
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

fn build_enemy_party(wave: u32, boss_wave: bool, elite: bool) -> Vec<Combatant> {
    let extra = ((wave.saturating_sub(1) / 3).min(3)) as usize;
    let count = 2 + extra + if elite { 1 } else { 0 };
    let names = [
        "Thicket Slime",
        "Bramble Bat",
        "Glow Wisp",
        "Rootling",
        "Mossling",
    ];
    (0..count)
        .map(|index| {
            let boss = boss_wave && index == 0;
            let base_health = if boss {
                30u32.saturating_add(wave.saturating_mul(3))
            } else {
                8u32.saturating_add(wave.saturating_mul(2))
            };
            let base_health = if elite && !boss { base_health.saturating_mul(5) / 4 } else { base_health };
            let attack = if boss {
                4u32.saturating_add(wave / 3)
            } else {
                2u32.saturating_add(wave / 5).saturating_add(if elite { 1 } else { 0 })
            };
            Combatant {
                id: u64::MAX.saturating_sub(index as u64),
                name: if boss {
                    "Mosswood Sentinel".to_string()
                } else {
                    names[index % names.len()].to_string()
                },
                class: None,
                attack,
                max_health: base_health,
                current_health: base_health,
                initiative: if boss { 7 } else { 4 + (index % 2) as u8 },
                boss,
            }
        })
        .collect()
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


    fn set_route(game: &mut GameState, kind: RouteNodeKind) {
        game.phase = RunPhase::Intermission;
        game.pending_event = None;
        game.pending_route = Some(vec![RouteOption {
            id: format!("test-route-{}", game.wave),
            kind,
            title: "Test route".to_string(),
            description: "A test path option.".to_string(),
        }]);
    }

    fn set_journey_event(game: &mut GameState, kind: JourneyEventKind) {
        game.phase = RunPhase::Intermission;
        game.pending_event = Some(JourneyEvent {
            id: format!("test-event-{}", game.wave),
            wave: game.wave,
            kind,
            title: "Test encounter".to_string(),
            description: "A test encounter with two choices.".to_string(),
            choices: vec![
                JourneyChoice {
                    label: "Choice A".to_string(),
                    description: "First effect".to_string(),
                },
                JourneyChoice {
                    label: "Choice B".to_string(),
                    description: "Second effect".to_string(),
                },
            ],
        });
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
        assert!(game.pending_event.is_some());
        game.resolve_journey_event(0).unwrap();
        game.choose_route(0).unwrap();
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
        game.resolve_journey_event(1).unwrap();
        game.choose_route(0).unwrap();
        assert!(game.next_wave().is_ok());
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
        game.resolve_journey_event(1).unwrap();
        game.choose_route(0).unwrap();
        assert!(game.next_wave().is_ok());
    }
    #[test]
    fn battle_generates_deterministic_timeline_for_same_seed() {
        let mut a = run(301);
        let mut b = run(301);
        let left = a.battle().unwrap();
        let right = b.battle().unwrap();
        assert_eq!(left, right);
        assert!(
            left.events
                .iter()
                .any(|event| event.kind == BattleEventKind::AllyAttack)
        );
        assert_eq!(
            left.events.last().unwrap().kind,
            BattleEventKind::BattleEnded
        );
    }

    #[test]
    fn defeat_removes_fallen_allies_and_records_their_loss() {
        let mut game = run(302);
        game.units.truncate(1);
        game.units[0].attack = 1;
        game.units[0].health = 1;
        let report = game.battle().unwrap();
        assert!(!report.victory);
        assert!(
            report
                .events
                .iter()
                .any(|event| event.kind == BattleEventKind::AllyDefeated)
        );
        assert!(game.units.is_empty());
    }

    #[test]
    fn guardian_is_targeted_before_backline_units() {
        let mut game = run(303);
        let guardian_id = game.units[0].id;
        game.units[0].attack = 1;
        let mut archer = game.spawn_unit(UnitClass::Archer);
        archer.attack = 1;
        let archer_id = archer.id;
        game.units.push(archer);
        game.battle().unwrap();
        let first_enemy_attack = game
            .last_battle
            .as_ref()
            .unwrap()
            .events
            .iter()
            .find(|event| event.kind == BattleEventKind::EnemyAttack)
            .unwrap();
        assert_eq!(first_enemy_attack.target_id, guardian_id);
        assert_ne!(first_enemy_attack.target_id, archer_id);
    }

    #[test]
    fn cleric_emits_healing_events_when_an_ally_is_wounded() {
        let mut game = run(304);
        let guardian = &mut game.units[0];
        guardian.current_health = Some(5);
        let cleric = game.spawn_unit(UnitClass::Cleric);
        game.units.push(cleric);
        let report = game.battle().unwrap();
        assert!(
            report
                .events
                .iter()
                .any(|event| event.kind == BattleEventKind::UnitHealed)
        );
    }

    #[test]
    fn next_wave_restores_a_small_amount_of_survivor_health() {
        let mut game = run(305);
        game.phase = RunPhase::Intermission;
        let unit = game.units.first_mut().unwrap();
        unit.health = 20;
        unit.current_health = Some(5);
        game.next_wave().unwrap();
        assert_eq!(game.units[0].current_health, Some(7));
    }

    #[test]
    fn cache_choice_grants_gold_and_persists_the_outcome() {
        let mut game = run(501);
        set_journey_event(&mut game, JourneyEventKind::LostCache);
        game.resolve_journey_event(0).unwrap();
        assert_eq!(game.gold, 570);
        assert!(game.pending_event.is_none());
        assert_eq!(game.event_history.last().unwrap().choice_index, 0);
    }

    #[test]
    fn shrine_choice_heals_survivors_and_charges_the_declared_cost() {
        let mut game = run(502);
        game.units[0].health = 20;
        game.units[0].current_health = Some(4);
        set_journey_event(&mut game, JourneyEventKind::MoonwellShrine);
        game.resolve_journey_event(0).unwrap();
        assert_eq!(game.gold, 440);
        assert_eq!(game.units[0].current_health, Some(8));
    }

    #[test]
    fn shrine_blessing_increases_every_survivors_attack() {
        let mut game = run(503);
        let before = game.units[0].attack;
        set_journey_event(&mut game, JourneyEventKind::MoonwellShrine);
        game.resolve_journey_event(1).unwrap();
        assert_eq!(game.units[0].attack, before + 2);
    }

    #[test]
    fn merchant_purchase_spends_gold_and_adds_the_item() {
        let mut game = run(504);
        set_journey_event(&mut game, JourneyEventKind::TravellingMerchant);
        game.resolve_journey_event(0).unwrap();
        assert_eq!(game.gold, 420);
        assert!(game.items.contains(&ItemKind::SharpeningStone));
    }

    #[test]
    fn wounded_ranger_can_join_when_capacity_allows() {
        let mut game = run(505);
        let count = game.units.len();
        set_journey_event(&mut game, JourneyEventKind::WoundedRanger);
        game.resolve_journey_event(0).unwrap();
        assert_eq!(game.units.len(), count + 1);
        assert_eq!(game.gold, 450);
    }

    #[test]
    fn bandit_standoff_trades_one_heart_for_gold() {
        let mut game = run(506);
        set_journey_event(&mut game, JourneyEventKind::BanditAmbush);
        game.resolve_journey_event(1).unwrap();
        assert_eq!(game.gold, 590);
        assert_eq!(game.hearts, 4);
    }

    #[test]
    fn failed_event_purchase_keeps_encounter_open_without_partial_mutation() {
        let mut game = run(507);
        game.gold = 0;
        set_journey_event(&mut game, JourneyEventKind::TravellingMerchant);
        assert_eq!(game.resolve_journey_event(0), Err(GameError::NotEnoughGold));
        assert_eq!(game.gold, 0);
        assert!(game.pending_event.is_some());
        assert!(game.event_history.is_empty());
    }

    #[test]
    fn full_roster_cannot_recruit_from_wounded_ranger() {
        let mut game = run(508);
        while game.units.len() < game.unit_limit {
            let donor = game.spawn_unit(UnitClass::Archer);
            game.units.push(donor);
        }
        let gold_before = game.gold;
        set_journey_event(&mut game, JourneyEventKind::WoundedRanger);
        assert_eq!(
            game.resolve_journey_event(0),
            Err(GameError::UnitCapacityReached)
        );
        assert_eq!(game.gold, gold_before);
        assert_eq!(game.units.len(), game.unit_limit);
        assert!(game.pending_event.is_some());
    }


    #[test]
    fn route_fork_is_seeded_and_has_three_distinct_options() {
        let mut a = run(601);
        let mut b = run(601);
        a.battle().unwrap();
        b.battle().unwrap();
        a.resolve_journey_event(0).unwrap();
        b.resolve_journey_event(0).unwrap();
        assert_eq!(a.pending_route, b.pending_route);
        let options = a.pending_route.as_ref().unwrap();
        assert_eq!(options.len(), 3);
        let mut kinds: Vec<RouteNodeKind> = options.iter().map(|option| option.kind).collect();
        kinds.sort_by_key(|kind| match kind {
            RouteNodeKind::Battle => 0,
            RouteNodeKind::Rest => 1,
            RouteNodeKind::Merchant => 2,
            RouteNodeKind::Elite => 3,
            RouteNodeKind::BossGate => 4,
        });
        kinds.dedup();
        assert_eq!(kinds.len(), 3);
    }

    #[test]
    fn rest_route_heals_the_party_and_restores_a_heart() {
        let mut game = run(602);
        game.hearts = 3;
        game.units[0].health = 20;
        game.units[0].current_health = Some(4);
        set_route(&mut game, RouteNodeKind::Rest);
        game.choose_route(0).unwrap();
        assert_eq!(game.hearts, 4);
        assert_eq!(game.units[0].current_health, Some(9));
        assert_eq!(game.current_route, Some(RouteNodeKind::Rest));
        assert!(game.pending_route.is_none());
        assert_eq!(game.route_history.len(), 1);
    }

    #[test]
    fn merchant_route_grants_gold_and_is_recorded() {
        let mut game = run(603);
        let before = game.gold;
        set_route(&mut game, RouteNodeKind::Merchant);
        game.choose_route(0).unwrap();
        assert_eq!(game.gold, before + 75);
        assert_eq!(game.route_history[0].kind, RouteNodeKind::Merchant);
    }

    #[test]
    fn elite_route_changes_battle_difficulty_and_report() {
        let mut elite = run(604);
        let mut standard = run(604);
        elite.units[0].attack = 100;
        standard.units[0].attack = 100;
        set_route(&mut elite, RouteNodeKind::Elite);
        set_route(&mut standard, RouteNodeKind::Battle);
        elite.choose_route(0).unwrap();
        standard.choose_route(0).unwrap();
        elite.next_wave().unwrap();
        standard.next_wave().unwrap();
        let elite_report = elite.battle().unwrap();
        let standard_report = standard.battle().unwrap();
        assert_eq!(elite_report.route, Some(RouteNodeKind::Elite));
        assert_eq!(standard_report.route, Some(RouteNodeKind::Battle));
        assert!(elite_report.enemy_power > standard_report.enemy_power);
        assert!(elite_report.gold_awarded >= standard_report.gold_awarded);
    }

    #[test]
    fn route_selection_rejects_replay_and_invalid_indices() {
        let mut game = run(605);
        set_route(&mut game, RouteNodeKind::Battle);
        assert_eq!(game.choose_route(9), Err(GameError::InvalidRouteChoice));
        game.choose_route(0).unwrap();
        assert_eq!(game.choose_route(0), Err(GameError::NoJourneyRoute));
    }

    #[test]
    fn boss_gate_is_only_offered_for_a_boss_wave() {
        let mut game = run(606);
        set_route(&mut game, RouteNodeKind::BossGate);
        assert_eq!(game.choose_route(0), Err(GameError::InvalidRouteChoice));
        game.wave = 4;
        game.pending_route.as_mut().unwrap()[0].id = "test-route-5".to_string();
        game.choose_route(0).unwrap();
        game.next_wave().unwrap();
        let report = game.battle().unwrap();
        assert!(report.boss);
        assert_eq!(report.route, Some(RouteNodeKind::BossGate));
    }

    #[test]
    fn journey_event_is_seeded_and_reproducible() {
        let mut a = run(411);
        let mut b = run(411);
        a.battle().unwrap();
        b.battle().unwrap();
        assert_eq!(a.pending_event, b.pending_event);
        assert!(a.pending_event.as_ref().unwrap().choices.len() >= 2);
    }

    #[test]
    fn journey_event_must_be_resolved_before_next_wave() {
        let mut game = run(412);
        game.battle().unwrap();
        if game.phase == RunPhase::Intermission {
            assert_eq!(game.next_wave(), Err(GameError::JourneyEventRequired));
            game.resolve_journey_event(0).unwrap();
            assert!(game.pending_event.is_none());
            assert_eq!(game.next_wave(), Err(GameError::JourneyRouteRequired));
            game.choose_route(0).unwrap();
            assert!(game.next_wave().is_ok());
        }
    }

    #[test]
    fn journey_event_rejects_invalid_and_replayed_choices() {
        let mut game = run(413);
        game.battle().unwrap();
        if game.pending_event.is_some() {
            assert_eq!(
                game.resolve_journey_event(99),
                Err(GameError::InvalidJourneyChoice)
            );
            game.resolve_journey_event(0).unwrap();
            assert_eq!(
                game.resolve_journey_event(0),
                Err(GameError::NoJourneyEvent)
            );
            assert_eq!(game.event_history.len(), 1);
        }
    }

    #[test]
    fn resolved_journey_event_is_recorded_with_choice_and_outcome() {
        let mut game = run(414);
        game.battle().unwrap();
        if game.pending_event.is_some() {
            game.resolve_journey_event(0).unwrap();
            let resolution = game.event_history.last().unwrap();
            assert_eq!(resolution.event_id, format!("wave-{}-event", game.wave));
            assert_eq!(resolution.choice_index, 0);
            assert!(!resolution.outcome.is_empty());
        }
    }

    #[test]
    fn boss_timeline_contains_telegraph_events() {
        let mut game = run(306);
        game.wave = 5;
        let report = game.battle().unwrap();
        assert!(report.boss);
        assert!(
            report
                .events
                .iter()
                .any(|event| event.kind == BattleEventKind::BossTelegraph)
        );
    }
}
