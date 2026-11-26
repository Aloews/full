extends Node2D

const PAPER := Color("#F5E9BD")
const PAPER_SHADE := Color("#D9B47A")
const INK := Color("#2B2638")
const SAGE := Color("#5E9B58")
const CLAY := Color("#E87958")
const HONEY := Color("#F3C969")
const BLUE := Color("#72B9D2")
const BERRY := Color("#A66DA6")
const CREAM := Color("#F5E9BD")

var elapsed := 0.0
var run_id := ""
var run_snapshot: Dictionary = {}
var api_request: HTTPRequest
var pending_action := ""
var api_busy := false
var server_url := ""
var status_text := "CONNECTING TO GAME SERVER"
var next_status_text := ""
var draw_button: Button
var battle_button: Button
var status_label: Label
var relic_panel: Panel
var relic_title: Label
var relic_buttons: Array[Button] = []
var battle_frames: Array = []
var battle_frame_index := 0
var battle_replay_timer := 0.0
var battle_replay_active := false
var battle_frame_events: Array = []
var visual_hp: Dictionary = {}
var visual_max_hp: Dictionary = {}
var visual_hit_flash: Dictionary = {}
var visual_heal_flash: Dictionary = {}
var visual_lunge: Dictionary = {}

var fate_pattern := [
    [0, 1, 0, 3],
    [2, 1, 4, 3],
    [2, 5, 4, 0],
    [3, 5, 2, 1]
]
var fate_colors := [SAGE, CLAY, BLUE, Color("#A99B82"), BERRY, HONEY]

func _ready() -> void:
    get_window().min_size = Vector2i(640, 360)
    server_url = OS.get_environment("CASINO_BATTLE_API")
    if server_url.is_empty():
        server_url = "http://127.0.0.1:3000"
    server_url = server_url.trim_suffix("/")

    api_request = HTTPRequest.new()
    add_child(api_request)
    api_request.request_completed.connect(_on_request_completed)
    _setup_controls()
    _create_run()

func _setup_controls() -> void:
    var layer := CanvasLayer.new()
    layer.layer = 10
    add_child(layer)

    var root := Control.new()
    root.set_anchors_preset(Control.PRESET_TOP_LEFT)
    root.position = Vector2.ZERO
    root.size = Vector2(1280, 720)
    root.scale = Vector2(0.5, 0.5)
    layer.add_child(root)

    status_label = Label.new()
    status_label.position = Vector2(810, 568)
    status_label.custom_minimum_size = Vector2(230, 18)
    status_label.add_theme_font_size_override("font_size", 10)
    status_label.add_theme_color_override("font_color", Color(INK, 0.74))
    root.add_child(status_label)

    draw_button = Button.new()
    draw_button.text = "DRAW SIGILS"
    draw_button.position = Vector2(810, 590)
    draw_button.custom_minimum_size = Vector2(178, 32)
    _style_button(draw_button, HONEY)
    draw_button.pressed.connect(_on_draw_pressed)
    root.add_child(draw_button)

    battle_button = Button.new()
    battle_button.text = "AUTO-BATTLE"
    battle_button.position = Vector2(810, 628)
    battle_button.custom_minimum_size = Vector2(178, 32)
    _style_button(battle_button, SAGE)
    battle_button.pressed.connect(_on_battle_pressed)
    root.add_child(battle_button)

    relic_panel = Panel.new()
    relic_panel.position = Vector2(260, 235)
    relic_panel.size = Vector2(760, 230)
    relic_panel.visible = false
    var relic_style := StyleBoxFlat.new()
    relic_style.bg_color = Color("#F8F2E7")
    relic_style.border_color = INK
    relic_style.set_border_width_all(2)
    relic_style.set_corner_radius_all(12)
    relic_panel.add_theme_stylebox_override("panel", relic_style)
    root.add_child(relic_panel)

    relic_title = Label.new()
    relic_title.position = Vector2(24, 22)
    relic_title.size = Vector2(710, 32)
    relic_title.text = "A NEW CHARM FOR THE JOURNEY"
    relic_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    relic_title.add_theme_font_size_override("font_size", 17)
    relic_title.add_theme_color_override("font_color", INK)
    relic_panel.add_child(relic_title)

    _update_controls()

func _style_button(button: Button, fill: Color) -> void:
    var normal := StyleBoxFlat.new()
    normal.bg_color = fill
    normal.border_color = INK
    normal.set_border_width_all(1)
    normal.set_corner_radius_all(0)
    normal.content_margin_left = 10
    normal.content_margin_right = 10
    normal.content_margin_top = 5
    normal.content_margin_bottom = 5

    var hover := normal.duplicate()
    hover.bg_color = fill.lightened(0.08)
    var pressed := normal.duplicate()
    pressed.bg_color = fill.darkened(0.08)
    var disabled := normal.duplicate()
    disabled.bg_color = PAPER_SHADE
    disabled.border_color = Color(INK, 0.25)

    button.add_theme_stylebox_override("normal", normal)
    button.add_theme_stylebox_override("hover", hover)
    button.add_theme_stylebox_override("pressed", pressed)
    button.add_theme_stylebox_override("disabled", disabled)
    button.add_theme_color_override("font_color", INK)
    button.add_theme_color_override("font_hover_color", INK)
    button.add_theme_color_override("font_pressed_color", INK)
    button.add_theme_color_override("font_disabled_color", Color(INK, 0.4))
    button.add_theme_font_size_override("font_size", 12)

func _create_run() -> void:
    _send_request("create", HTTPClient.METHOD_POST, "/api/v1/runs", "{}")

func _refresh_run() -> void:
    if run_id.is_empty():
        return
    _send_request("refresh", HTTPClient.METHOD_GET, "/api/v1/runs/%s" % run_id, "")

func _send_request(action: String, method: int, path: String, body: String) -> void:
    if api_busy:
        return
    api_busy = true
    pending_action = action
    status_text = "CONTACTING THE SERVER"
    var headers := PackedStringArray(["Content-Type: application/json"])
    var error := api_request.request(server_url + path, headers, method, body)
    if error != OK:
        api_busy = false
        pending_action = ""
        status_text = "SERVER NOT REACHABLE"
    _update_controls()
    queue_redraw()

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    api_busy = false
    var action := pending_action
    pending_action = ""

    if result != HTTPRequest.RESULT_SUCCESS:
        status_text = "SERVER OFFLINE · RUN API"
        _update_controls()
        queue_redraw()
        return

    if response_code < 200 or response_code >= 300:
        status_text = "SERVER ERROR · %d" % response_code
        _update_controls()
        queue_redraw()
        return

    var payload = JSON.parse_string(body.get_string_from_utf8())
    if not (payload is Dictionary):
        status_text = "INVALID SERVER RESPONSE"
        _update_controls()
        queue_redraw()
        return

    match action:
        "create":
            run_id = str(payload.get("run_id", ""))
            _apply_run_snapshot(payload.get("state", {}))
            status_text = "CONNECTED · RUN READY"
        "draw":
            _apply_board(payload.get("board", []))
            var clusters: Array = payload.get("matches", [])
            next_status_text = "FATE DRAW · %d CLUSTERS" % clusters.size()
            _refresh_run()
        "battle":
            var won := bool(payload.get("victory", false))
            var next_wave := int(payload.get("wave", 1))
            next_status_text = ("VICTORY · WAVE %02d" % next_wave) if won else "THE PARTY NEEDS REST"
            _start_battle_replay(payload.get("events", []))
        "formation":
            _apply_run_snapshot(payload)
            status_text = "FORMATION UPDATED"
        "relic":
            _apply_run_snapshot(payload)
            status_text = "RELIC EQUIPPED · READY FOR THE NEXT WAVE"
        "refresh":
            _apply_run_snapshot(payload)
            status_text = next_status_text if not next_status_text.is_empty() else "CONNECTED · PREPARATION"
            next_status_text = ""
        _:
            status_text = "CONNECTED"

    _update_controls()
    queue_redraw()

func _apply_run_snapshot(snapshot: Dictionary) -> void:
    run_snapshot = snapshot
    _apply_board(snapshot.get("board", []))
    _update_relic_panel()

func _apply_board(board: Array) -> void:
    var indices := {
        "leaf": 0,
        "ember": 1,
        "tide": 2,
        "stone": 3,
        "moon": 4,
        "wing": 5
    }
    for row in range(mini(4, board.size())):
        if not (board[row] is Array):
            continue
        for col in range(mini(4, board[row].size())):
            fate_pattern[row][col] = int(indices.get(str(board[row][col]), 0))

func _start_battle_replay(events: Array) -> void:
    battle_frames.clear()
    battle_frame_index = 0
    battle_frame_events.clear()
    visual_hp.clear()
    visual_max_hp.clear()
    visual_hit_flash.clear()
    visual_heal_flash.clear()
    visual_lunge.clear()

    for unit in run_snapshot.get("party", []):
        var unit_id := int(unit.get("id", 0))
        visual_hp[unit_id] = int(unit.get("hp", 1))
        visual_max_hp[unit_id] = int(unit.get("max_hp", 1))

    var wave := int(run_snapshot.get("wave", 1))
    var enemy_count := mini(3 + int(maxi(0, wave - 1) / 2), 8)
    for enemy_index in range(enemy_count):
        var enemy_id := 9223372036854775807 - enemy_index
        var enemy_hp := 16 + wave * 4 + enemy_index * 3
        if wave % 3 == 0 and enemy_index == 0:
            enemy_hp *= 3
        visual_hp[enemy_id] = enemy_hp
        visual_max_hp[enemy_id] = enemy_hp

    var frames_by_tick: Dictionary = {}
    for event in events:
        var tick := int(event.get("tick", 0))
        if not frames_by_tick.has(tick):
            frames_by_tick[tick] = []
        frames_by_tick[tick].append(event)

    var ticks: Array = frames_by_tick.keys()
    ticks.sort()
    for tick in ticks:
        battle_frames.append({
            "tick": int(tick),
            "events": frames_by_tick[tick]
        })

    if battle_frames.is_empty():
        battle_replay_active = false
        _refresh_run()
        return

    battle_replay_active = true
    battle_replay_timer = 0.01
    status_text = "AUTO-BATTLE · TICK 00"
    _update_controls()
    queue_redraw()

func _advance_battle_replay() -> void:
    if battle_frame_index >= battle_frames.size():
        battle_replay_active = false
        battle_frame_events.clear()
        _update_controls()
        _refresh_run()
        return

    var frame: Dictionary = battle_frames[battle_frame_index]
    battle_frame_index += 1
    battle_frame_events = frame.get("events", [])
    status_text = "AUTO-BATTLE · TICK %02d" % int(frame.get("tick", 0))

    for event in battle_frame_events:
        var kind := str(event.get("kind", "attack"))
        var source_id := int(event.get("source_unit_id", 0))
        var target_id := int(event.get("target_unit_id", 0))
        var amount := int(event.get("amount", 0))
        if not visual_hp.has(target_id):
            continue

        if kind == "attack":
            visual_lunge[source_id] = 0.15
            visual_hit_flash[target_id] = 0.18
            visual_hp[target_id] = maxi(0, int(visual_hp[target_id]) - amount)
        elif kind == "heal":
            visual_heal_flash[target_id] = 0.24
            visual_hp[target_id] = mini(
                int(visual_max_hp.get(target_id, visual_hp[target_id])),
                int(visual_hp[target_id]) + amount
            )
        elif kind == "defeat":
            visual_hp[target_id] = 0

    battle_replay_timer = 0.115
    _update_controls()
    queue_redraw()

func _unit_position(unit_id: int) -> Vector2:
    var party: Array = run_snapshot.get("party", [])
    var lane_counts := [0, 0, 0]

    for unit in party:
        var lane := clampi(int(unit.get("lane", 0)), 0, 2)
        var stack := int(lane_counts[lane])
        var position := Vector2(300.0 + stack * 60.0, 258.0 + lane * 88.0)
        if int(unit.get("id", 0)) == unit_id:
            return position
        lane_counts[lane] = stack + 1

    var largest_enemy_id := 9223372036854775807
    if unit_id >= largest_enemy_id - 7:
        var enemy_index := largest_enemy_id - unit_id
        return Vector2(850.0 + float(enemy_index / 3) * 62.0, 258.0 + float(enemy_index % 3) * 88.0)

    return Vector2(0, 0)

func _draw_battle_effects() -> void:
    for event in battle_frame_events:
        var source_id := int(event.get("source_unit_id", 0))
        var target_id := int(event.get("target_unit_id", 0))
        var source := _unit_position(source_id)
        var target := _unit_position(target_id)
        if source == Vector2.ZERO or target == Vector2.ZERO:
            continue

        source = _pixel_point(source)
        target = _pixel_point(target)
        var kind := str(event.get("kind", "attack"))
        var amount := int(event.get("amount", 0))

        if kind == "attack":
            draw_rect(Rect2(source + Vector2(22, -2), Vector2(maxf(2.0, absf(target.x - source.x) - 42.0), 4)), CLAY)
            draw_rect(Rect2(target + Vector2(-10, -10), Vector2(20, 4)), Color(CLAY, 0.35))
            draw_rect(Rect2(target + Vector2(-4, -16), Vector2(8, 16)), Color(CLAY, 0.35))
            draw_rect(Rect2(target + Vector2(-14, -25), Vector2(4, 4)), HONEY)
            draw_string(ThemeDB.fallback_font, _pixel_point(target + Vector2(-14, -25)), "-%d" % amount, HORIZONTAL_ALIGNMENT_CENTER, 32, 16, CLAY)
        elif kind == "heal":
            draw_rect(Rect2(source + Vector2(18, -2), Vector2(maxf(2.0, absf(target.x - source.x) - 36.0), 4)), SAGE.lightened(0.18))
            draw_rect(Rect2(target + Vector2(-10, -10), Vector2(20, 4)), Color(SAGE, 0.35))
            draw_rect(Rect2(target + Vector2(-2, -16), Vector2(4, 16)), SAGE.lightened(0.18))
            draw_string(ThemeDB.fallback_font, _pixel_point(target + Vector2(-14, -25)), "+%d" % amount, HORIZONTAL_ALIGNMENT_CENTER, 32, 16, SAGE.darkened(0.2))
        elif kind == "defeat":
            draw_rect(Rect2(target + Vector2(-12, -2), Vector2(24, 4)), HONEY)
            draw_rect(Rect2(target + Vector2(-2, -12), Vector2(4, 24)), HONEY)
            draw_rect(Rect2(target + Vector2(-8, -8), Vector2(4, 4)), HONEY)
            draw_rect(Rect2(target + Vector2(4, 4), Vector2(4, 4)), HONEY)

func _update_relic_panel() -> void:
    if not is_instance_valid(relic_panel):
        return

    var choices: Array = run_snapshot.get("pending_relics", [])
    var show_choices := str(run_snapshot.get("phase", "preparation")) == "relic_choice" and not choices.is_empty()
    relic_panel.visible = show_choices

    for button in relic_buttons:
        button.queue_free()
    relic_buttons.clear()

    if not show_choices:
        return

    relic_title.text = "A NEW CHARM FOR THE JOURNEY"
    for index in range(choices.size()):
        var relic := str(choices[index])
        var button := Button.new()
        button.text = _relic_label(relic)
        button.position = Vector2(24 + index * 240, 104)
        button.size = Vector2(220, 76)
        _style_button(button, HONEY if index == 0 else (SAGE if index == 1 else BLUE))
        button.add_theme_font_size_override("font_size", 11)
        button.pressed.connect(_on_relic_selected.bind(relic))
        relic_panel.add_child(button)
        relic_buttons.append(button)

func _relic_label(relic: String) -> String:
    match relic:
        "honey_bell":
            return "HONEY BELL\n+1 ATTACK"
        "clover_mantle":
            return "CLOVER MANTLE\n+4 MAX HP"
        "thorn_badge":
            return "THORN BADGE\n+1 ARMOR"
        "swift_feather":
            return "SWIFT FEATHER\nFASTER ATTACKS"
        "tidesong_thread":
            return "TIDESONG THREAD\n+2 SUPPORT HEAL"
        _:
            return relic.to_upper()

func _on_relic_selected(relic: String) -> void:
    if run_id.is_empty() or api_busy:
        return
    var body := JSON.stringify({"relic": relic})
    _send_request("relic", HTTPClient.METHOD_POST, "/api/v1/runs/%s/relic" % run_id, body)

func _on_draw_pressed() -> void:
    if run_id.is_empty():
        return
    _send_request("draw", HTTPClient.METHOD_POST, "/api/v1/runs/%s/draw" % run_id, "{}")

func _on_battle_pressed() -> void:
    if run_id.is_empty():
        return
    _send_request("battle", HTTPClient.METHOD_POST, "/api/v1/runs/%s/battle" % run_id, "{}")

func _unhandled_input(event: InputEvent) -> void:
    if not (event is InputEventMouseButton):
        return
    if not event.pressed or event.button_index != MOUSE_BUTTON_LEFT:
        return
    if api_busy or battle_replay_active or run_id.is_empty():
        return
    if str(run_snapshot.get("phase", "preparation")) != "preparation":
        return

    for unit in run_snapshot.get("party", []):
        var unit_id := int(unit.get("id", 0))
        var center := _unit_position(unit_id)
        if (event.position * 2.0).distance_to(center) <= 43.0:
            var next_lane := (int(unit.get("lane", 0)) + 1) % 3
            var request_body := JSON.stringify({
                "unit_id": unit_id,
                "lane": next_lane
            })
            _send_request(
                "formation",
                HTTPClient.METHOD_POST,
                "/api/v1/runs/%s/formation" % run_id,
                request_body
            )
            return

func _update_controls() -> void:
    if not is_instance_valid(draw_button):
        return
    var active := str(run_snapshot.get("phase", "preparation")) == "preparation"
    var essence := int(run_snapshot.get("essence", 0))
    draw_button.disabled = api_busy or run_id.is_empty() or not active or essence <= 0
    battle_button.disabled = api_busy or battle_replay_active or run_id.is_empty() or not active or run_snapshot.get("party", []).is_empty()
    status_label.text = status_text

func _decay_visual_timers(timers: Dictionary, delta: float) -> void:
    for unit_id in timers.keys():
        var remaining := float(timers[unit_id]) - delta
        if remaining <= 0.0:
            timers.erase(unit_id)
        else:
            timers[unit_id] = remaining

func _process(delta: float) -> void:
    elapsed += delta
    _decay_visual_timers(visual_hit_flash, delta)
    _decay_visual_timers(visual_heal_flash, delta)
    _decay_visual_timers(visual_lunge, delta)
    if battle_replay_active:
        battle_replay_timer -= delta
        if battle_replay_timer <= 0.0:
            _advance_battle_replay()
    queue_redraw()

func _draw() -> void:
    # Render a 1280x720 design canvas into the 640x360 viewport at exact 2x pixels.
    draw_set_transform(Vector2.ZERO, 0.0, Vector2(0.5, 0.5))
    var design_size := Vector2(1280, 720)
    draw_rect(Rect2(Vector2.ZERO, design_size), PAPER)
    _draw_paper_grain(design_size)
    _draw_header()
    _draw_battlefield(design_size)
    _draw_party_strip(design_size)

func _draw_paper_grain(size: Vector2) -> void:
    for i in range(120):
        var x := fmod(float(i * 137 + 41), size.x)
        var y := fmod(float(i * 71 + 19), size.y)
        var pixel := _pixel_point(Vector2(x, y))
        draw_rect(Rect2(pixel, Vector2(2, 2)), Color("#694653", 0.09))

func _draw_header() -> void:
    var wave := int(run_snapshot.get("wave", 1))
    var hearts := int(run_snapshot.get("hearts", 3))
    draw_string(ThemeDB.fallback_font, Vector2(48, 52), "THE MOSS MEADOW", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, INK)
    draw_string(ThemeDB.fallback_font, Vector2(48, 80), "A little party, a very big adventure", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(INK, 0.65))
    draw_string(ThemeDB.fallback_font, Vector2(48, 101), "TAP A FRIEND TO CHANGE ITS LANE", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(INK, 0.52))
    draw_string(ThemeDB.fallback_font, Vector2(1120, 52), "WAVE %02d" % wave, HORIZONTAL_ALIGNMENT_RIGHT, 180, 17, INK)
    draw_string(ThemeDB.fallback_font, Vector2(1120, 78), "♥  %d" % hearts, HORIZONTAL_ALIGNMENT_RIGHT, 180, 15, CLAY)

func _draw_battlefield(size: Vector2) -> void:
    var arena := Rect2(Vector2(70, 120), Vector2(size.x - 140, 400))
    draw_rect(arena, Color("#5E9B58"))
    draw_rect(arena, Color(INK, 0.8), false, 4.0)

    # Tile-like grass variation: all edges and coordinates land on the pixel grid.
    for row in range(12):
        for col in range(34):
            var tile_position := arena.position + Vector2(col * 32.0, row * 32.0)
            if tile_position.x + 32.0 > arena.end.x or tile_position.y + 32.0 > arena.end.y:
                continue
            var pattern := (row * 13 + col * 7) % 9
            if pattern == 0:
                draw_rect(Rect2(tile_position + Vector2(8, 8), Vector2(8, 4)), Color("#78B861", 0.65))
            elif pattern == 1:
                draw_rect(Rect2(tile_position + Vector2(20, 20), Vector2(4, 4)), Color("#467F4D", 0.55))
            elif pattern == 2:
                draw_rect(Rect2(tile_position + Vector2(4, 24), Vector2(4, 4)), Color("#9BCB69", 0.48))

    for lane in range(3):
        var lane_y := 258.0 + lane * 88.0
        draw_rect(Rect2(Vector2(112, lane_y - 27), Vector2(size.x - 224, 54)), Color("#467F4D", 0.16))
        draw_string(
            ThemeDB.fallback_font,
            Vector2(88, lane_y + 4),
            "I" if lane == 0 else ("II" if lane == 1 else "III"),
            HORIZONTAL_ALIGNMENT_LEFT,
            24,
            9,
            Color("#F5E9BD", 0.78)
        )
        if lane < 2:
            draw_rect(Rect2(Vector2(108, lane_y + 42), Vector2(size.x - 216, 2)), Color("#2B2638", 0.24))

    _draw_pixel_plant(Vector2(145, 450), 1)
    _draw_pixel_plant(Vector2(1100, 185), 1)
    _draw_pixel_plant(Vector2(720, 470), 0)

    var party: Array = run_snapshot.get("party", [])
    for unit in party:
        var unit_id := int(unit.get("id", 0))
        var position := _unit_position(unit_id)
        var name := str(unit.get("name", "Mossguard"))
        var max_hp := maxi(1, int(unit.get("max_hp", 1)))
        var current_hp := int(visual_hp.get(unit_id, unit.get("hp", max_hp)))
        var health_ratio := clampf(float(current_hp) / float(max_hp), 0.0, 1.0)
        _draw_creature(
            position,
            _sigil_color(str(unit.get("sigil", "leaf"))),
            name,
            true,
            1.0,
            health_ratio,
            unit_id
        )

    var wave := int(run_snapshot.get("wave", 1))
    var enemy_count := mini(3 + int(maxi(0, wave - 1) / 2), 8)
    for enemy_index in range(enemy_count):
        var enemy_id := 9223372036854775807 - enemy_index
        var enemy_position := _unit_position(enemy_id)
        var is_boss := wave % 3 == 0 and enemy_index == 0
        var enemy_name := "Mosswood Guardian" if is_boss else ("Gloomling" if enemy_index % 2 == 0 else "Murkling")
        var enemy_color := HONEY if is_boss else (BERRY if enemy_index % 2 == 0 else Color("#8C8B9C"))
        var enemy_base_hp := 16 + wave * 4 + enemy_index * 3
        var enemy_fallback_hp := enemy_base_hp * 3 if is_boss else enemy_base_hp
        var enemy_max_hp := maxi(1, int(visual_max_hp.get(enemy_id, enemy_fallback_hp)))
        var enemy_hp := int(visual_hp.get(enemy_id, enemy_max_hp))
        _draw_creature(
            enemy_position,
            enemy_color,
            enemy_name,
            false,
            1.5 if is_boss else 1.0,
            clampf(float(enemy_hp) / float(enemy_max_hp), 0.0, 1.0),
            enemy_id
        )

    var bob := roundf(sin(elapsed * 2.1) * 2.0)
    draw_rect(Rect2(Vector2(310, 287 + bob), Vector2(36, 2)), Color("#F3C969", 0.7))
    _draw_leaf_sprinkle(Vector2(250, 210), 1)
    _draw_leaf_sprinkle(Vector2(1060, 465), 0)
    if battle_replay_active:
        _draw_battle_effects()

func _draw_creature(
    center: Vector2,
    coat: Color,
    label: String,
    friendly: bool,
    scale_factor: float,
    health_ratio: float = 1.0,
    unit_id: int = 0
) -> void:
    var pixel_step := 4.0 if label == "Mosswood Guardian" else 2.0
    var blink_phase := fposmod(elapsed + float(unit_id % 7) * 0.43, 3.8)
    var bob := roundf(sin(elapsed * 2.5 + center.x * 0.01) * 2.0) * 2.0
    var lunge_timer := float(visual_lunge.get(unit_id, 0.0))
    var lunge_progress := clampf(lunge_timer / 0.15, 0.0, 1.0)
    var lunge_offset := roundf(sin((1.0 - lunge_progress) * PI) * 6.0 / pixel_step) * pixel_step
    var side := 1.0 if friendly else -1.0
    var c := center + Vector2(lunge_offset * side, bob)
    var rows := _creature_pixels(label)
    if blink_phase < 0.13:
        for row_index in range(rows.size()):
            if rows[row_index].contains("e"):
                rows[row_index] = rows[row_index].replace("e", "b")
    var sprite_size := 16.0 * pixel_step
    var origin := Vector2(
        roundf(c.x / pixel_step) * pixel_step - sprite_size / 2.0,
        roundf(c.y / pixel_step) * pixel_step - sprite_size / 2.0
    )
    var palette := _creature_palette(coat, label)
    var hit_timer := float(visual_hit_flash.get(unit_id, 0.0))
    var heal_timer := float(visual_heal_flash.get(unit_id, 0.0))
    if hit_timer > 0.0:
        var hit_strength := clampf(hit_timer / 0.18, 0.0, 1.0)
        palette["b"] = coat.lerp(CREAM, hit_strength * 0.72)
        palette["s"] = coat.darkened(0.48).lerp(CREAM, hit_strength * 0.38)

    if heal_timer > 0.0:
        var heal_alpha := clampf(heal_timer / 0.24, 0.0, 1.0) * 0.72
        draw_rect(Rect2(origin + Vector2(-4, -4), Vector2(sprite_size + 8, 2)), Color(SAGE, heal_alpha))
        draw_rect(Rect2(origin + Vector2(-4, sprite_size + 2), Vector2(sprite_size + 8, 2)), Color(SAGE, heal_alpha))
        draw_rect(Rect2(origin + Vector2(-4, -2), Vector2(2, sprite_size + 4)), Color(SAGE, heal_alpha))
        draw_rect(Rect2(origin + Vector2(sprite_size + 2, -2), Vector2(2, sprite_size + 4)), Color(SAGE, heal_alpha))

    if hit_timer > 0.0:
        var flash_alpha := clampf(hit_timer / 0.18, 0.0, 1.0) * 0.78
        draw_rect(Rect2(origin + Vector2(-4, -4), Vector2(sprite_size + 8, 2)), Color(HONEY, flash_alpha))

    draw_rect(
        Rect2(Vector2(c.x - 14.0, c.y + sprite_size / 2.0 - 1.0), Vector2(28.0 * (pixel_step / 2.0), 3.0)),
        Color(INK, 0.28)
    )

    for row_index in range(rows.size()):
        var row: String = rows[row_index]
        for column_index in range(row.length()):
            var pixel := row.substr(column_index, 1)
            if pixel == ".":
                continue
            var color: Color = palette.get(pixel, coat)
            var pixel_position := origin + Vector2(column_index * pixel_step, row_index * pixel_step)
            draw_rect(Rect2(pixel_position, Vector2(pixel_step, pixel_step)), color)

    _draw_nameplate(c, label, friendly, scale_factor, health_ratio)

func _creature_pixels(label: String) -> PackedStringArray:
    match label:
        "Mossguard":
            return PackedStringArray([
                ".......a........",
                "......aaa.......",
                ".....aabaa......",
                "...kkkkkkkkkk...",
                "..kssssssssssk..",
                ".kssbbbbbbbbssk.",
                ".kssbbhbbhbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbeebbeebbssk",
                "kssbbppbbppbbssk",
                "kssbbbbbbbbbbssk",
                ".kssbbbbbbbbssk.",
                "..kkk....kkk....",
                "..ksk....ksk....",
                "................",
                "................"
            ])
        "Cinderkit":
            return PackedStringArray([
                "....k......k....",
                "...ksk....ksk...",
                "...kssk..kssk...",
                "...kkkkkkkkkk...",
                "..kssssssssssk..",
                ".kssbbbbbbbbssk.",
                ".kssbbhbbhbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbeebbeebbssk",
                "kssbbppbbppbbssk",
                "kssbbbbbbbbbbssk",
                ".kssbbbbbbbbssk.",
                "..kkk......kkk..",
                "..ksk......ksk..",
                "................",
                "................"
            ])
        "Puddlekin":
            return PackedStringArray([
                ".......k........",
                "......ksk.......",
                ".....ksbsk......",
                "....ksbbbsk.....",
                "...ksbbbbbsk....",
                "..ksbbhbbbhsk...",
                "..ksbbeebbesk...",
                ".ksbbbbbbbbbsk..",
                ".ksbbppbbbppsk..",
                ".ksbbbbbbbbbsk..",
                ".ksbbbbbbbbbsk..",
                "..ksssssssssk...",
                "...kkkkkkkkk....",
                ".....aa.........",
                "....aaha........",
                "................"
            ])
        "Pebbleback":
            return PackedStringArray([
                "......kkkk......",
                "....kksssskk....",
                "...kssssssssk...",
                "..kssssssssssk..",
                ".kssssssssssssk.",
                ".kssbbbbbbbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbhbbbbhbbssk",
                "kssbbbbbbbbbbssk",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                ".kssbbbbbbbbssk.",
                "..kksssssssskk..",
                "...kkk....kkk...",
                "...ksk....ksk...",
                "................"
            ])
        "Moonmote":
            return PackedStringArray([
                ".......a........",
                "......aaa.......",
                ".....aaaaa......",
                "....akkkka......",
                "...aksssska.....",
                "..akssbbsska....",
                ".akssbbbbsska...",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                "kssbbppbbppbbssk",
                ".kssbbbbbbbbssk.",
                "..kksssssssskk..",
                "...kkk....kkk...",
                "...ksk....ksk...",
                "................",
                "................"
            ])
        "Breezeling":
            return PackedStringArray([
                "...a............",
                "..aaa...........",
                ".aabaa..........",
                "...kkkkkkkkkk...",
                "..kssssssssssk..",
                ".kssbbbbbbbbssk.",
                ".kssbbhbbhbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbeebbeebbssk",
                "kssbbppbbppbbssk",
                ".kssbbbbbbbbssk.",
                "..kssbbbbbbssk..",
                "...kkk....kkk...",
                "...ksk....ksk...",
                "................",
                "................"
            ])
        "Gloomling":
            return PackedStringArray([
                "................",
                "....aaaa........",
                "...akkkka.......",
                "..aksssska......",
                ".aksssssska.....",
                ".kkkkkkkkkk.....",
                "..ksssssssskk...",
                ".kssbbbbbbbbssk.",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                "kssbbppbbppbbssk",
                ".kssbbbbbbbbssk.",
                "..kkk....kkk....",
                "..ksk....ksk....",
                "................",
                "................"
            ])
        "Murkling":
            return PackedStringArray([
                "................",
                ".....kkkk.......",
                "...kksssskk.....",
                "..ksssssssskk...",
                ".ksssssssssssk..",
                ".kssbbbbbbbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbhbbbbhbbssk",
                "kssbbbbbbbbbbssk",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                ".kssbbbbbbbbssk.",
                "..kksssssssskk..",
                "...kkk....kkk...",
                "...ksk....ksk...",
                "................"
            ])
        "Mosswood Guardian":
            return PackedStringArray([
                "......a..a......",
                ".....aaa.aaa....",
                "....akkkka......",
                "...aksssska.....",
                "..aksssssska....",
                ".kkkkkkkkkkkkkk.",
                ".ksssssssssssssk",
                "kssbbbbbbbbbbssk",
                "kssbbhbbbbhbbssk",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                "kssbbppbbppbbssk",
                ".kssbbbbbbbbssk.",
                "..kksssssssskk..",
                "...kkk....kkk...",
                "...ksk....ksk..."
            ])
        _:
            return PackedStringArray([
                "................",
                "................",
                "......kkkk......",
                "....kksssskk....",
                "...ksssssssk....",
                "..ksssssssssk...",
                ".kssbbbbbbbbssk.",
                "kssbbbbbbbbbbssk",
                "kssbbhbbbbhbbssk",
                "kssbbeebbeebbssk",
                "kssbbbbbbbbbbssk",
                ".kssbbbbbbbbssk.",
                "..kksssssssskk..",
                "...kkk....kkk...",
                "...ksk....ksk...",
                "................"
            ])

func _creature_palette(coat: Color, label: String) -> Dictionary:
    var accent := HONEY
    if label == "Puddlekin":
        accent = Color("#B7E3D0")
    elif label == "Moonmote":
        accent = Color("#F3C969")
    elif label == "Gloomling":
        accent = Color("#D4A1BE")
    elif label == "Murkling" or label == "Pebbleback":
        accent = Color("#B9B8C7")
    return {
        "k": INK,
        "s": coat.darkened(0.48),
        "b": coat,
        "h": coat.lightened(0.32),
        "a": accent,
        "e": Color("#241F2E"),
        "p": Color("#F2A18E")
    }

func _draw_nameplate(center: Vector2, label: String, friendly: bool, s: float, health_ratio: float) -> void:
    var baseline := _pixel_point(Vector2(center.x, center.y + 48.0 * s)).y
    var text_position := _pixel_point(Vector2(center.x - 54.0 * s, baseline))
    draw_string(ThemeDB.fallback_font, text_position, label, HORIZONTAL_ALIGNMENT_CENTER, 108.0 * s, 12, INK)
    var bar_position := _pixel_point(Vector2(center.x - 21.0 * s, baseline + 7.0))
    var bar := Rect2(bar_position, Vector2(roundf(42.0 * s / 2.0) * 2.0, 4.0))
    draw_rect(bar, Color(INK, 0.35))
    var fill_width := roundf(bar.size.x * clampf(health_ratio, 0.0, 1.0) / 2.0) * 2.0
    if fill_width > 0.0:
        draw_rect(Rect2(bar.position, Vector2(fill_width, bar.size.y)), SAGE if friendly else CLAY)

func _draw_pixel_plant(position: Vector2, variation: int) -> void:
    var p := _pixel_point(position)
    var trunk_color := Color("#694653")
    draw_rect(Rect2(p + Vector2(-4, -26), Vector2(8, 28)), trunk_color)
    draw_rect(Rect2(p + Vector2(-12, -38), Vector2(24, 12)), SAGE.darkened(0.08))
    draw_rect(Rect2(p + Vector2(-18, -32), Vector2(12, 12)), SAGE)
    draw_rect(Rect2(p + Vector2(6, -44), Vector2(12, 14)), Color("#78B861"))
    draw_rect(Rect2(p + Vector2(-8, -50), Vector2(16, 10)), Color("#9BCB69"))
    draw_rect(Rect2(p + Vector2(-12, -26), Vector2(6, 4)), Color("#9BCB69"))
    if variation == 1:
        draw_rect(Rect2(p + Vector2(12, -30), Vector2(6, 4)), HONEY)

func _draw_leaf_sprinkle(position: Vector2, variation: int) -> void:
    var p := _pixel_point(position)
    var color := Color("#9BCB69", 0.8) if variation == 1 else Color("#F3C969", 0.8)
    draw_rect(Rect2(p, Vector2(4, 2)), color)
    draw_rect(Rect2(p + Vector2(2, -2), Vector2(2, 6)), color)
    draw_rect(Rect2(p + Vector2(6, 2), Vector2(4, 2)), color)

func _draw_party_strip(size: Vector2) -> void:
    var panel := Rect2(Vector2(70, 555), Vector2(size.x - 140, 112))
    draw_rect(panel, CREAM)
    draw_rect(Rect2(panel.position, panel.size), INK, false, 2.0)
    draw_string(ThemeDB.fallback_font, Vector2(92, 580), "YOUR LITTLE PARTY", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, INK)

    var party: Array = run_snapshot.get("party", [])
    for i in range(mini(6, party.size())):
        var unit: Dictionary = party[i]
        var x := 96.0 + i * 116.0
        var sigil := str(unit.get("sigil", "leaf"))
        _draw_sigil_icon(Vector2(x, 620), sigil, _sigil_color(sigil))
        draw_string(
            ThemeDB.fallback_font,
            Vector2(x + 17, 617),
            str(unit.get("name", "Friend")),
            HORIZONTAL_ALIGNMENT_LEFT,
            94,
            10,
            INK
        )
        draw_string(
            ThemeDB.fallback_font,
            Vector2(x + 17, 632),
            "RANK %d" % int(unit.get("rank", 1)),
            HORIZONTAL_ALIGNMENT_LEFT,
            94,
            9,
            Color(INK, 0.72)
        )

    _draw_fate_preview(Vector2(size.x - 185, 574))
    draw_string(ThemeDB.fallback_font, Vector2(size.x - 95, 671), "PREPARE  >  AUTO-BATTLE", HORIZONTAL_ALIGNMENT_RIGHT, 300, 11, INK)

func _sigil_color(sigil: String) -> Color:
    match sigil:
        "leaf":
            return SAGE
        "ember":
            return CLAY
        "tide":
            return BLUE
        "stone":
            return Color("#A99B82")
        "moon":
            return BERRY
        "wing":
            return HONEY
        _:
            return PAPER_SHADE

func _draw_fate_preview(origin: Vector2) -> void:
    origin = _pixel_point(origin)
    draw_string(ThemeDB.fallback_font, origin + Vector2(-4, 0), "FATE BOARD", HORIZONTAL_ALIGNMENT_LEFT, 110, 10, INK)
    var tile_size := 16.0
    var gap := 6.0
    var sigils := ["leaf", "ember", "tide", "stone", "moon", "wing"]
    for row in range(4):
        for col in range(4):
            var tile_origin := origin + Vector2(col * (tile_size + gap), 10 + row * (tile_size + gap))
            var color := fate_colors[fate_pattern[row][col]]
            draw_rect(Rect2(tile_origin, Vector2(tile_size, tile_size)), Color("#D9B47A"))
            draw_rect(Rect2(tile_origin, Vector2(tile_size, tile_size)), INK, false, 2.0)
            var sigil := sigils[fate_pattern[row][col]]
            _draw_sigil_icon(tile_origin + Vector2(3, 3), sigil, color)

func _draw_sigil_icon(origin: Vector2, sigil: String, color: Color) -> void:
    origin = _pixel_point(origin)
    var rows: PackedStringArray
    match sigil:
        "leaf":
            rows = PackedStringArray(["..a..", ".aaa.", "aabab", ".aaa.", "..a.."])
        "ember":
            rows = PackedStringArray(["..a..", ".aaa.", ".aba.", "aabaa", ".aaa."])
        "tide":
            rows = PackedStringArray(["..a..", ".aaa.", "aaaaa", ".aaa.", "..a.."])
        "stone":
            rows = PackedStringArray([".aaa.", "aaaaa", "ababa", "aaaaa", ".aaa."])
        "moon":
            rows = PackedStringArray([".aaa.", "aa...", "aa...", "aa...", ".aaa."])
        "wing":
            rows = PackedStringArray(["....a", "...aa", "..aba", ".abba", "a..a."])
        _:
            rows = PackedStringArray([".....", ".aaa.", ".aba.", ".aaa.", "....."])

    var palette := {"a": color, "b": color.lightened(0.35)}
    var pixel_size := 2.0
    for row_index in range(rows.size()):
        var row: String = rows[row_index]
        for column_index in range(row.length()):
            var pixel := row.substr(column_index, 1)
            if pixel == ".":
                continue
            draw_rect(
                Rect2(origin + Vector2(column_index * pixel_size, row_index * pixel_size), Vector2(pixel_size, pixel_size)),
                palette.get(pixel, color)
            )

func _pixel_point(point: Vector2) -> Vector2:
    return Vector2(roundf(point.x / 2.0) * 2.0, roundf(point.y / 2.0) * 2.0)
