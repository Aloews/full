'use strict';

const $ = (id) => document.getElementById(id);
const PIXEL_PALETTES = {
  guardian: { ink: '#2B2638', main: '#5E9B58', light: '#9BC477', shadow: '#3F714C', skin: '#F5E9BD', accent: '#F3C969' },
  archer: { ink: '#2B2638', main: '#5E9B58', light: '#9BC477', shadow: '#3F714C', skin: '#F5E9BD', accent: '#E87958' },
  mage: { ink: '#2B2638', main: '#A66DA6', light: '#D5A9D0', shadow: '#754C7D', skin: '#F5E9BD', accent: '#72B9D2' },
  cleric: { ink: '#2B2638', main: '#72B9D2', light: '#B7E0E2', shadow: '#4F8294', skin: '#F5E9BD', accent: '#F3C969' },
  rogue: { ink: '#2B2638', main: '#754C7D', light: '#A66DA6', shadow: '#513854', skin: '#F5E9BD', accent: '#E87958' },
  beast: { ink: '#2B2638', main: '#9A6545', light: '#D7A36A', shadow: '#67432F', skin: '#F5E9BD', accent: '#5E9B58' },
};

function paintWorldScene() {
  const canvas = $('world-scene');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.imageSmoothingEnabled = false;
  const px = (x, y, w, h, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w, h);
  };
  const colors = {
    sky: '#72b9d2', dusk: '#4f8294', mountain: '#3d5b55', mountainLight: '#6f9870',
    deep: '#243d38', tree: '#315b42', leaf: '#5e9b58', leafLight: '#9bc477',
    trunk: '#805638', ground: '#456b43', grass: '#9bc477', stone: '#8a8b70',
    stoneLight: '#d8d09d', shadow: '#2b2638', gold: '#f3c969', window: '#f6dfa0'
  };
  px(0, 0, 320, 64, colors.sky);
  px(0, 0, 320, 18, colors.dusk);
  // Distant stars and a blocky crescent moon.
  [[18,10],[42,22],[77,9],[116,17],[160,8],[205,18],[248,10],[291,21]].forEach(([x,y],i) =>
    px(x, y, i % 3 === 0 ? 2 : 1, i % 3 === 0 ? 2 : 1, colors.window));
  px(270, 7, 8, 8, colors.gold); px(272, 5, 6, 2, colors.gold);
  px(276, 9, 4, 5, colors.dusk);
  // Stepped mountain silhouettes.
  [[0,31,42,12],[30,25,48,18],[66,32,42,11],[190,29,44,14],[225,23,55,20],[278,31,42,12]].forEach(([x,y,w,h]) => {
    px(x,y,w,h,colors.mountain);
    px(x+8,y-4,w-16,4,colors.mountainLight);
  });
  // Woodland canopy layers.
  [[8,35],[35,31],[60,37],[235,35],[260,29],[292,36]].forEach(([x,y],i) => {
    px(x+5,y+10,5,13,colors.trunk);
    px(x,y+3,15,12,colors.deep);
    px(x+2,y,11,11,i%2?colors.leaf:colors.tree);
    px(x+4,y+2,4,3,colors.leafLight);
    px(x+12,y+7,3,4,colors.deep);
  });
  // Ground plane and stone path.
  px(0,48,320,16,colors.ground);
  for(let x=0;x<320;x+=16){px(x,48,8,2,colors.leaf);px(x+8,60,8,2,colors.deep);}
  [[133,50],[149,53],[165,50],[181,53],[197,50]].forEach(([x,y])=>px(x,y,12,6,colors.stone));
  [[138,51],[154,54],[170,51],[186,54],[202,51]].forEach(([x,y])=>px(x,y,5,2,colors.stoneLight));
  // Original rune shrine, built from chunky 16-bit stone tiles.
  px(103,27,34,25,colors.shadow); px(107,23,26,29,colors.stone);
  px(111,19,18,8,colors.stoneLight); px(115,15,10,5,colors.gold);
  px(112,29,16,23,colors.shadow); px(115,32,10,20,colors.deep);
  px(118,35,4,7,colors.gold); px(119,37,2,3,colors.window);
  px(99,49,42,5,colors.shadow); px(95,54,50,4,colors.stoneLight);
  // Small party silhouettes approaching the shrine.
  px(72,46,8,3,colors.shadow); px(74,39,5,7,colors.shadow);
  px(75,40,3,4,colors.leaf); px(73,47,3,5,colors.shadow); px(78,47,3,5,colors.shadow);
  px(218,47,7,3,colors.shadow); px(219,41,5,6,colors.shadow);
  px(220,42,3,3,colors.gold); px(218,48,3,4,colors.shadow); px(222,48,3,4,colors.shadow);
  // Grass tufts and firefly pixels.
  [[15,56],[53,52],[87,58],[145,59],[230,55],[282,53],[308,58]].forEach(([x,y]) => {
    px(x,y,2,4,colors.leafLight); px(x-2,y+2,2,2,colors.leaf);
  });
  [[91,29],[155,35],[208,27],[286,43]].forEach(([x,y])=>px(x,y,2,2,colors.gold));
}

function pixelSpriteMarkup(className, label) {
  const sprite = Object.prototype.hasOwnProperty.call(PIXEL_PALETTES, className) ? className : 'guardian';
  return `<canvas class="pixel-unit" width="16" height="16" data-sprite="${sprite}" role="img" aria-label="${esc(label)}"></canvas>`;
}
function paintPixelSprites() {
  document.querySelectorAll('canvas[data-sprite]').forEach((canvas) => {
    const ctx = canvas.getContext('2d');
    const palette = PIXEL_PALETTES[canvas.dataset.sprite];
    if (!ctx || !palette) return;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, 16, 16);
    const r = (x, y, w, h, color) => {
      ctx.fillStyle = color;
      ctx.fillRect(x, y, w, h);
    };
    const c = palette;
    if (canvas.dataset.sprite === 'guardian') {
      r(5, 1, 6, 2, c.ink); r(4, 3, 8, 4, c.ink); r(5, 3, 6, 3, c.main);
      r(6, 4, 1, 1, c.skin); r(9, 4, 1, 1, c.skin); r(7, 5, 2, 1, c.shadow);
      r(4, 7, 8, 5, c.ink); r(5, 8, 6, 3, c.main); r(6, 8, 2, 1, c.light);
      r(2, 8, 3, 4, c.ink); r(3, 9, 1, 2, c.skin);
      r(11, 7, 4, 6, c.ink); r(12, 8, 2, 4, c.accent); r(13, 9, 1, 2, c.light);
      r(5, 12, 2, 3, c.ink); r(9, 12, 2, 3, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
      r(5, 2, 6, 1, c.accent);
    } else if (canvas.dataset.sprite === 'archer') {
      r(5, 1, 7, 2, c.ink); r(4, 3, 8, 4, c.ink); r(5, 3, 6, 3, c.main);
      r(5, 2, 7, 1, c.light); r(6, 4, 1, 1, c.skin); r(9, 4, 1, 1, c.skin);
      r(4, 7, 8, 5, c.ink); r(5, 8, 6, 3, c.shadow); r(6, 8, 4, 1, c.main);
      r(2, 6, 2, 7, c.ink); r(3, 7, 1, 5, c.accent);
      r(12, 7, 1, 6, c.ink); r(13, 8, 1, 4, c.accent); r(14, 6, 1, 1, c.ink); r(14, 12, 1, 1, c.ink);
      r(5, 12, 2, 3, c.ink); r(9, 12, 2, 3, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
    } else if (canvas.dataset.sprite === 'mage') {
      r(6, 0, 4, 2, c.ink); r(5, 2, 6, 2, c.ink); r(4, 4, 8, 3, c.ink);
      r(6, 1, 4, 1, c.main); r(5, 3, 6, 1, c.light); r(5, 5, 6, 1, c.skin);
      r(4, 7, 8, 6, c.ink); r(5, 8, 6, 4, c.main); r(6, 8, 3, 1, c.light); r(8, 10, 2, 2, c.shadow);
      r(2, 8, 2, 4, c.ink); r(3, 9, 1, 2, c.main);
      r(12, 5, 2, 2, c.ink); r(13, 4, 2, 2, c.accent); r(14, 5, 1, 1, c.light);
      r(5, 13, 2, 2, c.ink); r(9, 13, 2, 2, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
    } else if (canvas.dataset.sprite === 'cleric') {
      r(6, 0, 4, 1, c.accent); r(5, 1, 6, 1, c.ink); r(4, 3, 8, 4, c.ink);
      r(5, 3, 6, 3, c.skin); r(6, 4, 1, 1, c.ink); r(9, 4, 1, 1, c.ink);
      r(4, 7, 8, 6, c.ink); r(5, 8, 6, 4, c.main); r(7, 8, 2, 3, c.light); r(7, 9, 2, 1, c.accent);
      r(2, 7, 2, 6, c.ink); r(3, 8, 1, 4, c.accent);
      r(12, 6, 2, 2, c.ink); r(13, 4, 1, 6, c.ink); r(12, 5, 3, 1, c.accent); r(13, 6, 1, 1, c.light);
      r(5, 13, 2, 2, c.ink); r(9, 13, 2, 2, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
    } else if (canvas.dataset.sprite === 'rogue') {
      r(4, 2, 8, 2, c.ink); r(3, 4, 10, 4, c.ink); r(5, 4, 6, 3, c.main);
      r(6, 5, 1, 1, c.skin); r(9, 5, 1, 1, c.skin); r(7, 6, 2, 1, c.shadow);
      r(4, 8, 8, 5, c.ink); r(5, 9, 6, 3, c.shadow); r(6, 9, 4, 1, c.main);
      r(2, 8, 3, 4, c.ink); r(3, 9, 2, 2, c.accent);
      r(12, 5, 2, 7, c.ink); r(13, 4, 1, 3, c.light); r(13, 8, 1, 3, c.accent);
      r(5, 13, 2, 2, c.ink); r(9, 13, 2, 2, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
    } else if (canvas.dataset.sprite === 'beast') {
      r(3, 2, 3, 4, c.ink); r(10, 2, 3, 4, c.ink); r(4, 3, 2, 2, c.accent); r(10, 3, 2, 2, c.accent);
      r(4, 5, 8, 6, c.ink); r(5, 6, 6, 4, c.main); r(6, 7, 1, 1, c.skin); r(9, 7, 1, 1, c.skin);
      r(7, 9, 3, 2, c.ink); r(8, 9, 1, 1, c.light);
      r(2, 9, 3, 3, c.ink); r(3, 10, 2, 1, c.shadow);
      r(11, 9, 3, 3, c.ink); r(12, 10, 2, 1, c.accent);
      r(4, 11, 8, 3, c.ink); r(5, 12, 6, 1, c.shadow);
      r(5, 13, 2, 2, c.ink); r(9, 13, 2, 2, c.ink); r(4, 14, 4, 1, c.shadow); r(8, 14, 4, 1, c.shadow);
    }
  });
}
const ITEM_META = {
  sharpening_stone: ['Sharpening Stone', 'Permanent army attack bonus'],
  vitality_charm: ['Vitality Charm', 'Reduce damage taken in a lost battle'],
  healing_potion: ['Healing Potion', 'Restore one heart'],
};
let game = null;
let keepId = null;
let busy = false;
let toastTimer = null;
let battleReplayToken = 0;

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.message || `Request failed (${response.status})`);
  return payload;
}

function notify(message) {
  const node = $('toast');
  node.textContent = message;
  node.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove('visible'), 2600);
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}

async function act(path, body) {
  if (!game || busy) return;
  busy = true;
  setControlsDisabled(true);
  try {
    game = await request(`/api/runs/${encodeURIComponent(game.run_id)}${path}`, {
      method: 'POST', body: body === undefined ? '{}' : JSON.stringify(body),
    });
    localStorage.setItem('slotbound-run-id', game.run_id);
    render();
  } catch (error) {
    notify(error.message);
  } finally {
    busy = false;
    setControlsDisabled(false);
    render();
  }
}

function setControlsDisabled(disabled) {
  document.querySelectorAll('button').forEach((button) => {
    if (!button.dataset.keepEnabled) button.disabled = disabled || button.dataset.disabled === 'true';
  });
}

async function startRun() {
  busy = true;
  setControlsDisabled(true);
  try {
    const seed = Math.floor(Math.random() * 2_000_000_000) + 1;
    game = await request('/api/runs', { method: 'POST', body: JSON.stringify({ seed }) });
    keepId = null;
    localStorage.setItem('slotbound-run-id', game.run_id);
    notify('A new run begins.');
    render();
  } catch (error) {
    notify(error.message);
  } finally {
    busy = false;
    setControlsDisabled(false);
    render();
  }
}

async function restoreRun() {
  const id = localStorage.getItem('slotbound-run-id');
  if (id) {
    try { game = await request(`/api/runs/${encodeURIComponent(id)}`); }
    catch { localStorage.removeItem('slotbound-run-id'); }
  }
  if (!game) {
    game = await request('/api/runs', { method: 'POST', body: JSON.stringify({ seed: 20261126 }) });
    localStorage.setItem('slotbound-run-id', game.run_id);
  }
  render();
}

function render() {
  if (!game) return;
  const lost = game.phase === 'lost';
  $('run-stats').innerHTML = `
    <div class="stat-chip"><span>GOLD</span><strong>◈ ${game.gold.toLocaleString()}</strong></div>
    <div class="stat-chip"><span>HEARTS</span><strong>${'♥'.repeat(game.hearts)}${'♡'.repeat(Math.max(0, 5 - game.hearts))}</strong></div>
    <div class="stat-chip"><span>WAVE</span><strong>${game.wave.toString().padStart(2, '0')}</strong></div>`;
  $('spins').innerHTML = `<span class="spin-dots">${'●'.repeat(game.spins_remaining)}${'○'.repeat(Math.max(0, 6-game.spins_remaining))}</span><small>${game.spins_remaining} draws left</small>`;
  $('spin-price').textContent = `NEXT DRAW · ${game.next_spin_cost} GOLD`;
  $('spin').disabled = lost || game.phase !== 'preparation' || game.spins_remaining === 0 || game.units.length > game.unit_limit || game.gold < game.next_spin_cost || busy;
  $('sigil-board').innerHTML = game.board.flatMap((row, r) => row.map((symbol, c) => {
    const meta = CLASS_META[symbol] || ['?', symbol, ''];
    const wins = game.last_spin?.wins?.some((win) => win.class === symbol && game.last_spin.board[r][c] === symbol);
    return `<div class="reel-cell ${wins ? 'reel-win' : ''}">${pixelSpriteMarkup(symbol, meta[1])}<small>${meta[1]}</small></div>`;
  })).join('');
  $('last-spin').textContent = game.last_spin
    ? `${game.last_spin.wins.length} winning line${game.last_spin.wins.length === 1 ? '' : 's'}${game.last_spin.jackpot ? ' · PERFECT RESONANCE' : ''}`
    : 'Match three symbols along a line';
  $('nudge-controls').innerHTML = [0,1,2].map((column) =>
    `<button class="button button-quiet button-small" data-action="nudge" data-column="${column}" data-direction="1" ${!game.nudge_available || !game.last_spin || game.phase !== 'preparation' || lost ? 'disabled' : ''}>SHIFT ${column + 1} ↕</button>`
  ).join('');
  $('unit-count').textContent = `${game.units.length} / ${game.unit_limit} SLOTS`;
  $('units').innerHTML = game.units.length ? game.units.map((unit) => renderUnit(unit)).join('') : '<div class="empty-state">No units in the formation.</div>';
  $('target-label').textContent = keepId ? `KEEPER #${keepId}` : 'NO KEEPER SELECTED';
  $('phase').textContent = game.phase.toUpperCase();
  $('battle-title').textContent = game.wave % 5 === 0 ? `Judgment wave ${game.wave}` : `Wave ${game.wave}`;
  renderBattle(lost);
  renderCores();
  renderShop();
  renderStatus();
  paintPixelSprites();
}

function renderUnit(unit) {
  const meta = CLASS_META[unit.class] || ['?', unit.class, ''];
  const keeper = keepId === unit.id;
  const canAct = ['preparation', 'intermission'].includes(game.phase) && !busy;
  return `<article class="unit-card ${keeper ? 'is-keeper' : ''}">
    <div class="unit-top"><span class="unit-symbol">${pixelSpriteMarkup(unit.class, meta[1])}</span><span class="unit-type">${esc(meta[2])}</span><button class="lock-button" data-action="lock" data-id="${unit.id}" aria-label="${unit.locked ? 'Unlock' : 'Lock'} ${esc(meta[1])}" ${!canAct ? 'disabled' : ''}>${unit.locked ? '🔒' : '⌑'}</button></div>
    <h3>${esc(unit.promotion || meta[1])}</h3><div class="unit-level">LV ${unit.level} · ABSORB ${unit.absorb_level}</div>
    <div class="unit-stats"><span>⚔ ${unit.attack}</span><span>♥ ${unit.current_health ?? unit.health} / ${unit.health}</span></div>
    <div class="unit-imprint">${unit.imprint ? `✦ ${esc(unit.imprint)}` : 'No imprint'}</div>
    ${unit.pending_promotion ? `<div class="promotion-options"><span>PROMOTION</span>${unit.promotion_options.map((name) => `<button class="button button-small" data-action="promote" data-id="${unit.id}" data-choice="${esc(name)}">${esc(name)}</button>`).join('')}</div>` : ''}
    <div class="unit-actions"><button class="button button-quiet button-small" data-action="keep" data-id="${unit.id}" ${!canAct || unit.locked ? 'disabled' : ''}>${keeper ? 'KEEPER SELECTED' : 'SELECT KEEPER'}</button><button class="button button-danger button-small" data-action="feed" data-id="${unit.id}" ${!canAct || unit.locked || !keepId || keepId === unit.id ? 'disabled' : ''}>FEED</button></div>
  </article>`;
}



function paintBattlefield(report, eventLimit) {
  const canvas = $('battlefield');
  if (!canvas || !report) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.imageSmoothingEnabled = false;
  const px = (x, y, w, h, color) => { ctx.fillStyle = color; ctx.fillRect(x, y, w, h); };
  px(0, 0, 320, 128, '#243d38');
  px(0, 0, 320, 54, '#4f8294');
  px(0, 54, 320, 74, '#456b43');
  for (let x = 0; x < 320; x += 16) {
    px(x, 54 + (x % 3) * 2, 8, 2, '#9bc477');
    px(x + 8, 116 - (x % 4) * 2, 8, 2, '#315b42');
  }
  px(154, 0, 2, 128, '#f3c969');
  px(156, 0, 1, 128, '#f5e9bd');
  const allEvents = report.events || [];
  const events = eventLimit === undefined ? allEvents : allEvents.slice(0, eventLimit);
  const actors = new Map();
  const normalizedName = (name) => String(name || '').replace(/ \(spell\)$/, '');
  const add = (id, name, team, health, amount = 0) => {
    if (!id || !name || name === 'Squad') return;
    const initial = Number.isFinite(health) ? Math.max(1, health + amount) : 20;
    const current = actors.get(id) || { id, name: normalizedName(name), team, hp: initial, max: initial, class: null, boss: false };
    current.name = normalizedName(name);
    current.team = team;
    if (Number.isFinite(health)) current.hp = Math.max(0, health);
    current.max = Math.max(current.max, (Number.isFinite(health) ? health : current.hp) + amount);
    actors.set(id, current);
  };
  (report.allies || []).forEach((unit) => {
    actors.set(unit.id, {
      id: unit.id, name: unit.name, team: 'ally',
      hp: unit.current_health, max: unit.max_health,
      class: unit.class, boss: Boolean(unit.boss),
    });
  });
  (report.enemies || []).forEach((unit) => {
    actors.set(unit.id, {
      id: unit.id, name: unit.name, team: 'enemy',
      hp: unit.current_health, max: unit.max_health,
      class: unit.class, boss: Boolean(unit.boss),
    });
  });
  events.forEach((entry) => {
    if (entry.kind === 'ally_attack') {
      add(entry.actor_id, entry.actor, 'ally');
      add(entry.target_id, entry.target, 'enemy', entry.remaining_health, entry.amount);
    }
    if (entry.kind === 'enemy_attack') {
      add(entry.actor_id, entry.actor, 'enemy');
      add(entry.target_id, entry.target, 'ally', entry.remaining_health, entry.amount);
    }
    if (entry.kind === 'enemy_defeated') add(entry.target_id, entry.target, 'enemy', 0);
    if (entry.kind === 'ally_defeated') add(entry.target_id, entry.target, 'ally', 0);
    if (entry.kind === 'unit_healed') add(entry.target_id, entry.target, 'ally', entry.remaining_health);
    if (entry.kind === 'boss_telegraph') add(entry.actor_id, entry.actor, 'enemy');
  });
  const allies = [...actors.values()].filter((unit) => unit.team === 'ally');
  const enemies = [...actors.values()].filter((unit) => unit.team === 'enemy');
  const positions = new Map();
  const allyColors = {
    guardian: '#9bc477', archer: '#e87958', mage: '#b88ac4',
    cleric: '#72b9d2', rogue: '#a66da6', beast: '#d7a36a',
  };
  const drawUnit = (unit, index, team) => {
    const x = team === 'ally' ? 22 + (index % 3) * 38 : 204 + (index % 3) * 34;
    const y = 67 + Math.floor(index / 3) * 25;
    positions.set(unit.id, { x: x + 12, y: y + 9 });
    const color = team === 'ally' ? (allyColors[unit.class] || '#9bc477') : (unit.boss ? '#b94c3e' : '#d77b59');
    px(x + 4, y, 12, 4, '#2b2638'); px(x + 2, y + 4, 16, 12, '#2b2638');
    px(x + 5, y + 2, 10, 5, color); px(x + 5, y + 7, 10, 7, color);
    px(x + 7, y + 4, 2, 2, '#f5e9bd'); px(x + 12, y + 4, 2, 2, '#f5e9bd');
    px(x + 5, y + 14, 4, 4, '#2b2638'); px(x + 12, y + 14, 4, 4, '#2b2638');
    px(x, y - 5, 24, 3, '#2b2638');
    px(x, y - 5, Math.max(0, Math.round(24 * unit.hp / Math.max(1, unit.max))), 3, team === 'ally' ? '#9bc477' : '#e87958');
    if (unit.boss) { px(x + 8, y - 11, 6, 4, '#f3c969'); }
  };
  allies.forEach((unit, index) => drawUnit(unit, index, 'ally'));
  enemies.forEach((unit, index) => drawUnit(unit, index, 'enemy'));
  const lastEvent = events[events.length - 1];
  if (lastEvent && ['ally_attack', 'enemy_attack', 'unit_healed'].includes(lastEvent.kind)) {
    const from = positions.get(lastEvent.actor_id);
    const to = positions.get(lastEvent.target_id);
    if (from && to) {
      ctx.strokeStyle = lastEvent.kind === 'unit_healed' ? '#9bc477' : '#f3c969';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke();
      px(to.x - 3, to.y - 3, 6, 6, lastEvent.kind === 'unit_healed' ? '#b7e0a1' : '#f3c969');
    }
  }
  if (lastEvent?.kind === 'boss_telegraph') {
    const boss = positions.get(lastEvent.actor_id);
    if (boss) {
      px(boss.x - 4, boss.y - 18, 8, 8, '#b94c3e');
      px(boss.x - 1, boss.y - 16, 2, 4, '#f5e9bd');
      px(boss.x - 1, boss.y - 11, 2, 2, '#f5e9bd');
    }
  }
  ctx.fillStyle = '#f5e9bd'; ctx.font = 'bold 7px monospace';
  ctx.fillText('YOUR PARTY', 12, 12); ctx.fillText(report.boss ? 'BOSS ENCOUNTER' : 'ENEMY PARTY', 214, 12);
  ctx.fillStyle = '#f3c969'; ctx.fillText('VS', 151, 15);
  if (!allies.length) { ctx.fillStyle = '#f5e9bd'; ctx.fillText('NO SURVIVORS', 12, 122); }
  if (!enemies.length) { ctx.fillStyle = '#f5e9bd'; ctx.fillText('CLEARED', 246, 122); }
}

function playBattleReplay(report) {
  const token = ++battleReplayToken;
  const events = report?.events || [];
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion || events.length < 2) {
    paintBattlefield(report);
    return;
  }
  let cursor = 0;
  const step = () => {
    if (token !== battleReplayToken) return;
    paintBattlefield(report, cursor);
    if (cursor >= events.length) return;
    cursor += 1;
    window.setTimeout(step, 115);
  };
  step();
}

function renderBattle(lost) {
  const report = game.last_battle;
  if (lost || game.phase !== 'intermission') battleReplayToken += 1;
  if (lost) {
    $('battle-content').innerHTML = '<div class="battle-result defeat"><strong>RUN ENDED</strong><span>Your defence has fallen.</span></div>';
    $('battle-actions').innerHTML = '<button class="button button-primary" id="restart">START NEW RUN</button>';
    $('restart').addEventListener('click', startRun);
    return;
  }
  if (game.phase === 'intermission' && report) {
    const timeline = (report.events || []).slice(-8).reverse().map((entry) => {
      const verbs = {
        ally_attack: 'strikes',
        enemy_attack: 'hits',
        ally_defeated: 'is defeated by',
        enemy_defeated: 'defeats',
        unit_healed: 'restores health to',
        boss_telegraph: 'telegraphs an attack at',
        battle_ended: 'ends the battle:',
      };
      const verb = verbs[entry.kind] || 'acts on';
      const amount = entry.amount ? ` · ${entry.kind === 'unit_healed' ? '+' : '-'}${entry.amount} HP` : '';
      return `<div class="combat-event ${esc(entry.kind)}"><span>R${entry.tick}</span><strong>${esc(entry.actor)}</strong> ${verb} <b>${esc(entry.target)}</b>${amount}</div>`;
    }).join('');
    const event = game.pending_event;
    const journeyMarkup = event ? `<section class="journey-event"><span class="eyebrow">JOURNEY ENCOUNTER · WAVE ${event.wave}</span><h3>${esc(event.title)}</h3><p>${esc(event.description)}</p><div class="journey-choices">${event.choices.map((choice, index) => { const costs = { moonwell_shrine: 60, travelling_merchant: 80, wounded_ranger: 50, bandit_ambush: 40 }; const cost = index === 0 ? (costs[event.kind] || 0) : 0; const blocked = game.gold < cost || (event.kind === "wounded_ranger" && index === 0 && game.units.length >= game.unit_limit); return `<button class="journey-choice" data-action="journey-choice" data-index="${index}" ${blocked ? "disabled" : ""}><strong>${esc(choice.label)}</strong><small>${esc(choice.description)}</small></button>`; }).join('')}</div></section>` : '';
    const latestOutcome = !event && game.event_history?.length ? `<div class="journey-outcome"><span class="eyebrow">JOURNEY CONSEQUENCE</span><strong>${esc(game.event_history[game.event_history.length - 1].outcome)}</strong></div>` : '';
    const route = game.pending_route || [];
    const routeMarkup = !event && route.length ? `<section class="route-fork"><div class="route-heading"><span class="eyebrow">CHOOSE YOUR PATH</span><strong>THE ROAD TO WAVE ${game.wave + 1}</strong></div><div class="route-branches">${route.map((option, index) => `<button class="route-option route-${esc(option.kind)}" data-action="route-choice" data-index="${index}"><span class="route-node">${option.kind === 'rest' ? '✚' : option.kind === 'merchant' ? '◈' : option.kind === 'elite' ? '⚔' : option.kind === 'boss_gate' ? '☠' : '➜'}</span><strong>${esc(option.title)}</strong><small>${esc(option.description)}</small></button>`).join('')}</div></section>` : '';
    $('battle-content').innerHTML = `<div class="battle-result ${report.victory ? 'victory' : 'defeat'}"><strong>${report.victory ? 'VICTORY' : 'DEFEAT'}</strong><span>${report.boss ? 'Boss encounter' : `Wave ${report.wave}`} · ${report.rounds || 0} rounds · ${game.units.length} survivors · ${report.route ? esc(report.route.replaceAll('_',' ')) + ' route' : 'main path'}</span><small>${report.victory ? `+${report.gold_awarded} gold` : `-${report.damage_taken} hearts · +${report.gold_awarded} gold`}</small></div><canvas id="battlefield" class="battlefield" width="320" height="128" role="img" aria-label="Pixel-art battlefield showing the last battle formation and combat health"></canvas>${journeyMarkup}${routeMarkup}${latestOutcome}<div class="combat-log"><span class="eyebrow">COMBAT LOG</span>${timeline || '<div class="empty-state">No combat events recorded.</div>'}</div>`;
    playBattleReplay(report);
    const blocked = Boolean(game.core_offer || event || game.pending_route);
    const buttonLabel = game.core_offer ? 'CHOOSE A CORE FIRST' : event ? 'RESOLVE JOURNEY EVENT' : game.pending_route ? 'CHOOSE A PATH FIRST' : 'PREPARE NEXT WAVE';
    $('battle-actions').innerHTML = `<button class="button button-quiet" data-action="replay-battle">REPLAY BATTLE</button><button class="button button-quiet" data-action="skip-replay">SKIP</button><button class="button button-primary" id="next-wave" ${blocked ? 'disabled' : ''}>${buttonLabel} <span>↗</span></button>`;
    $('next-wave').addEventListener('click', () => act('/next-wave'));
    return;
  }
  $('battle-content').innerHTML = `<div class="power-row"><div><small>READY UNITS</small><strong>${game.units.length}</strong></div><div class="versus">VS</div><div><small>ENCOUNTER</small><strong>${game.wave % 5 === 0 ? 'BOSS' : 'WAVE'}</strong></div></div><div class="enemy-line"><span>${game.wave % 5 === 0 ? '☠ JUDGMENT BOSS' : '⚔ ENEMY FRONT'}</span><span>Wave ${game.wave}</span></div>`;
  $('battle-actions').innerHTML = `<button class="button button-primary" id="start-battle" ${game.phase !== 'preparation' || busy ? 'disabled' : ''}>BEGIN BATTLE <span>↗</span></button>`;
  $('start-battle').addEventListener('click', () => act('/battle'));
}

function renderCores() {
  $('core-count').textContent = `${game.cores.length} / 8`;
  const current = game.cores.map((core) => `<div class="core-chip"><strong>${esc(core.replaceAll('_',' ').toUpperCase())}</strong><small>${core === 'fortune' ? '+15% battle gold' : core === 'might' ? '+12% army power' : '+1 unit capacity'}</small></div>`).join('');
  const offer = game.core_offer ? `<div class="offer-list"><span class="eyebrow">CHOOSE ONE</span>${game.core_offer.map((core, index) => `<button class="offer-card" data-action="core" data-index="${index}"><strong>${esc(core.replaceAll('_',' '))}</strong><small>${core === 'fortune' ? '+15% battle gold' : core === 'might' ? '+12% army power' : '+1 unit capacity'}</small></button>`).join('')}</div>` : '';
  $('cores').innerHTML = `${current || '<div class="empty-state">No cores equipped.</div>'}${offer}`;
}

function renderShop() {
  const enabled = game.phase === 'intermission' && !busy;
  $('shop').innerHTML = Object.entries(ITEM_META).map(([id, meta], index) => {
    const cost = game.shop_prices[index];
    return `<div class="shop-item"><div><strong>${meta[0]}</strong><small>${meta[1]}</small></div><button class="button button-small" data-action="buy" data-item="${id}" ${!enabled || game.gold < cost || (id === 'healing_potion' && game.hearts >= 5) ? 'disabled' : ''}>◈ ${cost}</button></div>`;
  }).join('');
}

function renderStatus() {
  $('status-list').innerHTML = `<div class="status-row"><span>Gold reserve</span><strong>◈ ${game.gold.toLocaleString()}</strong></div>
    <div class="status-row"><span>Defence integrity</span><strong>${game.hearts} / 5</strong></div>
    <div class="status-row"><span>Army capacity</span><strong>${game.units.length} / ${game.unit_limit}</strong></div>
    <div class="status-row"><span>Draws remaining</span><strong>${game.spins_remaining} / 6</strong></div>
    <div class="status-row"><span>Sigil shift</span><strong>${game.nudge_available ? 'READY' : 'USED'}</strong></div>
    <div class="status-row"><span>Items carried</span><strong>${game.items.length}</strong></div>
    <div class="status-row"><span>Journey events</span><strong>${game.event_history?.length || 0}</strong></div>`;
  if (game.last_battle) {
    const b = game.last_battle;
    $('field-report').textContent = `${b.victory ? 'Victory' : 'Defeat'} on wave ${b.wave} after ${b.rounds || 0} rounds. ${game.units.length} allies remain. ${b.victory ? `Earned ${b.gold_awarded} gold.` : `Lost ${b.damage_taken} hearts.`}`;
  } else if (game.last_spin) {
    $('field-report').textContent = `${game.last_spin.wins.length} sigil lines aligned. ${game.last_spin.wins.map((win) => CLASS_META[win.class][1]).join(', ') || 'No companions summoned.'}`;
  } else {
    $('field-report').textContent = 'The Fate Board is ready. Align three matching sigils to call a companion.';
  }
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button || !game || busy) return;
  const action = button.dataset.action;
  if (action === 'nudge') act('/nudge', { column: Number(button.dataset.column), direction: Number(button.dataset.direction) });
  if (action === 'keep') { keepId = Number(button.dataset.id); render(); }
  if (action === 'feed') {
    if (!keepId) { notify('Select a keeper first.'); return; }
    act('/absorb', { target_id: keepId, donor_id: Number(button.dataset.id) });
  }
  if (action === 'lock') act('/lock', { unit_id: Number(button.dataset.id) });
  if (action === 'promote') act('/promotion', { unit_id: Number(button.dataset.id), choice: button.dataset.choice });
  if (action === 'core') act('/core', { index: Number(button.dataset.index) });
  if (action === 'journey-choice') act('/event', { index: Number(button.dataset.index) });
  if (action === 'route-choice') act('/route', { index: Number(button.dataset.index) });
  if (action === 'replay-battle' && game.last_battle) playBattleReplay(game.last_battle);
  if (action === 'skip-replay' && game.last_battle) { battleReplayToken += 1; paintBattlefield(game.last_battle); }
  if (action === 'buy') act('/item', { item: button.dataset.item });
});

$('spin').addEventListener('click', () => act('/spin'));
$('new-run').addEventListener('click', startRun);
paintWorldScene();
restoreRun().catch((error) => notify(error.message));
