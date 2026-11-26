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
  $('spins').innerHTML = `<span class="spin-dots">${'●'.repeat(game.spins_remaining)}${'○'.repeat(Math.max(0, 6-game.spins_remaining))}</span><small>${game.spins_remaining} spins left</small>`;
  $('spin-price').textContent = `NEXT SPIN · ${game.next_spin_cost} GOLD`;
  $('spin').disabled = lost || game.phase !== 'preparation' || game.spins_remaining === 0 || game.units.length > game.unit_limit || game.gold < game.next_spin_cost || busy;
  $('reels').innerHTML = game.board.flatMap((row, r) => row.map((symbol, c) => {
    const meta = CLASS_META[symbol] || ['?', symbol, ''];
    const wins = game.last_spin?.wins?.some((win) => win.class === symbol && game.last_spin.board[r][c] === symbol);
    return `<div class="reel-cell ${wins ? 'reel-win' : ''}">${pixelSpriteMarkup(symbol, meta[1])}<small>${meta[1]}</small></div>`;
  })).join('');
  $('last-spin').textContent = game.last_spin
    ? `${game.last_spin.wins.length} winning line${game.last_spin.wins.length === 1 ? '' : 's'}${game.last_spin.jackpot ? ' · JACKPOT' : ''}`
    : 'Match three symbols along a line';
  $('nudge-controls').innerHTML = [0,1,2].map((column) =>
    `<button class="button button-quiet button-small" data-action="nudge" data-column="${column}" data-direction="1" ${!game.nudge_available || !game.last_spin || game.phase !== 'preparation' || lost ? 'disabled' : ''}>NUDGE ${column + 1} ↕</button>`
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
    <div class="unit-stats"><span>⚔ ${unit.attack}</span><span>♥ ${unit.health}</span></div>
    <div class="unit-imprint">${unit.imprint ? `✦ ${esc(unit.imprint)}` : 'No imprint'}</div>
    ${unit.pending_promotion ? `<div class="promotion-options"><span>PROMOTION</span>${unit.promotion_options.map((name) => `<button class="button button-small" data-action="promote" data-id="${unit.id}" data-choice="${esc(name)}">${esc(name)}</button>`).join('')}</div>` : ''}
    <div class="unit-actions"><button class="button button-quiet button-small" data-action="keep" data-id="${unit.id}" ${!canAct || unit.locked ? 'disabled' : ''}>${keeper ? 'KEEPER SELECTED' : 'SELECT KEEPER'}</button><button class="button button-danger button-small" data-action="feed" data-id="${unit.id}" ${!canAct || unit.locked || !keepId || keepId === unit.id ? 'disabled' : ''}>FEED</button></div>
  </article>`;
}


function renderBattle(lost) {
  const report = game.last_battle;
  if (lost) {
    $('battle-content').innerHTML = '<div class="battle-result defeat"><strong>RUN ENDED</strong><span>Your defence has fallen.</span></div>';
    $('battle-actions').innerHTML = '<button class="button button-primary" id="restart">START NEW RUN</button>';
    $('restart').addEventListener('click', startRun);
    return;
  }
  if (game.phase === 'intermission' && report) {
    $('battle-content').innerHTML = `<div class="battle-result ${report.victory ? 'victory' : 'defeat'}"><strong>${report.victory ? 'VICTORY' : 'DEFEAT'}</strong><span>${report.boss ? 'Judgment encounter' : `Wave ${report.wave}`} · ${report.army_power} power vs ${report.enemy_power}</span><small>${report.victory ? `+${report.gold_awarded} gold` : `-${report.damage_taken} heart · +${report.gold_awarded} gold`}</small></div>`;
    $('battle-actions').innerHTML = `<button class="button button-primary" id="next-wave" ${game.core_offer ? 'disabled' : ''}>${game.core_offer ? 'CHOOSE A CORE FIRST' : 'PREPARE NEXT WAVE'} <span>↗</span></button>`;
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
    <div class="status-row"><span>Spins remaining</span><strong>${game.spins_remaining} / 6</strong></div>
    <div class="status-row"><span>Machine nudge</span><strong>${game.nudge_available ? 'READY' : 'USED'}</strong></div>
    <div class="status-row"><span>Items carried</span><strong>${game.items.length}</strong></div>`;
  if (game.last_battle) {
    const b = game.last_battle;
    $('field-report').textContent = `${b.victory ? 'Victory' : 'Defeat'} on wave ${b.wave}. Army ${b.army_power}; enemy ${b.enemy_power}. ${b.victory ? `Earned ${b.gold_awarded} gold.` : `Lost ${b.damage_taken} heart.`}`;
  } else if (game.last_spin) {
    $('field-report').textContent = `${game.last_spin.wins.length} line matches. ${game.last_spin.wins.map((win) => CLASS_META[win.class][1]).join(', ') || 'No units summoned.'}`;
  } else {
    $('field-report').textContent = 'The machine is loaded. Recruit your formation before the wave begins.';
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
  if (action === 'buy') act('/item', { item: button.dataset.item });
});

$('spin').addEventListener('click', () => act('/spin'));
$('new-run').addEventListener('click', startRun);
restoreRun().catch((error) => notify(error.message));
