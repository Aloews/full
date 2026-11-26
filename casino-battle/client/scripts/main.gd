extends Node2D

const PAPER := Color("#F3EBDD")
const PAPER_SHADE := Color("#E7D9C2")
const INK := Color("#4A4540")
const SAGE := Color("#91A68A")
const CLAY := Color("#C77F62")
const HONEY := Color("#DDBB72")
const BLUE := Color("#8FAEBC")
const BERRY := Color("#9C7180")
const CREAM := Color("#F8F2E7")

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
    normal.set_corner_radius_all(7)
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
        var target_id := int(event.get("target_unit_id", 0))
        var amount := int(event.get("amount", 0))
        if not visual_hp.has(target_id):
            continue

        if kind == "attack":
            visual_hp[target_id] = maxi(0, int(visual_hp[target_id]) - amount)
        elif kind == "heal":
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

        var kind := str(event.get("kind", "attack"))
        var amount := int(event.get("amount", 0))
        if kind == "attack":
            draw_line(_pixel_point(source + Vector2(24, 0)), _pixel_point(target - Vector2(22, 0)), CLAY, 4.0, false)
            draw_circle(target, 18.0, Color(CLAY, 0.22))
            draw_string(ThemeDB.fallback_font, target + Vector2(-14, -25), "-%d" % amount, HORIZONTAL_ALIGNMENT_CENTER, 32, 16, CLAY)
        elif kind == "heal":
            draw_line(_pixel_point(source + Vector2(18, 0)), _pixel_point(target - Vector2(18, 0)), SAGE.lightened(0.18), 4.0, false)
            draw_circle(target, 19.0, Color(SAGE, 0.24))
            draw_string(ThemeDB.fallback_font, target + Vector2(-14, -25), "+%d" % amount, HORIZONTAL_ALIGNMENT_CENTER, 32, 16, SAGE.darkened(0.2))
        elif kind == "defeat":
            for angle in range(0, 360, 60):
                var direction := Vector2.from_angle(deg_to_rad(float(angle)))
                draw_line(target + direction * 13.0, target + direction * 24.0, HONEY, 2.0, true)

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

func _process(delta: float) -> void:
    elapsed += delta
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
    for i in range(90):
        var x := fmod(float(i * 137 + 41), size.x)
        var y := fmod(float(i * 71 + 19), size.y)
        draw_line(Vector2(x, y), Vector2(x + 2.0, y + 1.0), Color(0.35, 0.29, 0.22, 0.045), 1.0)

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
    draw_rect(arena, Color("#E9E0CF"))
    draw_rect(arena, Color(INK, 0.22), false, 2.0)

    for i in range(11):
        var x := arena.position.x + 24 + i * ((arena.size.x - 48) / 10.0)
        draw_line(Vector2(x, arena.position.y + 22), Vector2(x, arena.end.y - 22), Color(INK, 0.045), 1.0)

    for i in range(5):
        var y := arena.position.y + 24 + i * ((arena.size.y - 48) / 4.0)
        draw_line(Vector2(arena.position.x + 22, y), Vector2(arena.end.x - 22, y), Color(INK, 0.045), 1.0)

    for lane in range(3):
        var lane_y := 258.0 + lane * 88.0
        draw_string(
            ThemeDB.fallback_font,
            Vector2(88, lane_y + 4),
            "I" if lane == 0 else ("II" if lane == 1 else "III"),
            HORIZONTAL_ALIGNMENT_LEFT,
            24,
            9,
            Color(INK, 0.35)
        )

    _draw_plant(Vector2(145, 450), 1.0)
    _draw_plant(Vector2(1100, 185), 0.8)
    _draw_plant(Vector2(720, 470), 0.55)

    var party: Array = run_snapshot.get("party", [])
    var lane_counts := [0, 0, 0]
    for unit in party:
        var unit_id := int(unit.get("id", 0))
        var lane := clampi(int(unit.get("lane", 0)), 0, 2)
        var stack := int(lane_counts[lane])
        lane_counts[lane] = stack + 1
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
            0.92 if stack > 0 else 1.0,
            health_ratio
        )

    var wave := int(run_snapshot.get("wave", 1))
    var enemy_count := mini(3 + int(maxi(0, wave - 1) / 2), 8)
    for enemy_index in range(enemy_count):
        var enemy_id := 9223372036854775807 - enemy_index
        var enemy_position := _unit_position(enemy_id)
        var is_boss := wave % 3 == 0 and enemy_index == 0
        var enemy_name := "Mosswood Guardian" if is_boss else ("Gloomling" if enemy_index % 2 == 0 else "Murkling")
        var enemy_color := HONEY if is_boss else (BERRY if enemy_index % 2 == 0 else Color("#8D8578"))
        var enemy_base_hp := 16 + wave * 4 + enemy_index * 3
        var enemy_fallback_hp := enemy_base_hp * 3 if is_boss else enemy_base_hp
        var enemy_max_hp := maxi(1, int(visual_max_hp.get(enemy_id, enemy_fallback_hp)))
        var enemy_hp := int(visual_hp.get(enemy_id, enemy_max_hp))
        _draw_creature(
            enemy_position,
            enemy_color,
            enemy_name,
            false,
            0.88,
            clampf(float(enemy_hp) / float(enemy_max_hp), 0.0, 1.0)
        )

    var bob := sin(elapsed * 2.1) * 3.0
    draw_arc(Vector2(310, 288 + bob), 34.0, 0.0, TAU, 48, Color(HONEY, 0.48), 2.0)
    draw_circle(Vector2(850, 345), 34.0, Color(CLAY, 0.07))
    _draw_leaf_sprinkle(Vector2(250, 210), 0.7)
    _draw_leaf_sprinkle(Vector2(1060, 465), 0.55)
    if battle_replay_active:
        _draw_battle_effects()

func _draw_creature(center: Vector2, coat: Color, label: String, friendly: bool, scale_factor: float, health_ratio: float = 1.0) -> void:
    var bob := sin(elapsed * 2.5 + center.x * 0.01) * 2.5
    var c := center + Vector2(0, bob)
    var s := scale_factor

    draw_ellipse_placeholder(c + Vector2(0, 24) * s, Vector2(27, 7) * s, Color(INK, 0.12))
    draw_line(c + Vector2(-9, 17) * s, c + Vector2(-12, 27) * s, INK, 3.0 * s)
    draw_line(c + Vector2(9, 17) * s, c + Vector2(12, 27) * s, INK, 3.0 * s)

    match label:
        "Mossguard":
            _draw_mossguard(c, s, coat)
        "Cinderkit":
            _draw_cinderkit(c, s, coat)
        "Puddlekin":
            _draw_puddlekin(c, s, coat)
        "Pebbleback":
            _draw_pebbleback(c, s, coat)
        "Moonmote":
            _draw_moonmote(c, s, coat)
        "Breezeling":
            _draw_breezeling(c, s, coat)
        "Gloomling":
            _draw_gloomling(c, s, coat)
        "Mosswood Guardian":
            _draw_boss(c, s, coat)
        _:
            _draw_murkling(c, s, coat)

    _draw_nameplate(c, label, friendly, s, health_ratio)

func _draw_mossguard(c: Vector2, s: float, coat: Color) -> void:
    var shell := PackedVector2Array([
        c + Vector2(-25, 4) * s, c + Vector2(-21, -13) * s,
        c + Vector2(-8, -23) * s, c + Vector2(10, -23) * s,
        c + Vector2(24, -10) * s, c + Vector2(25, 8) * s,
        c + Vector2(12, 20) * s, c + Vector2(-13, 20) * s
    ])
    _outline(shell, Color("#718B70"), 2.4 * s)
    draw_arc(c + Vector2(0, -2) * s, 14.0 * s, PI, TAU, 24, Color("#D2C69D"), 1.4 * s)
    draw_circle(c + Vector2(-8, -5) * s, 2.2 * s, Color("#D2C69D"))
    draw_circle(c + Vector2(8, -5) * s, 2.2 * s, Color("#D2C69D"))

    var face := PackedVector2Array([
        c + Vector2(-18, 8) * s, c + Vector2(-18, -6) * s,
        c + Vector2(-8, -16) * s, c + Vector2(8, -16) * s,
        c + Vector2(18, -5) * s, c + Vector2(18, 9) * s,
        c + Vector2(9, 19) * s, c + Vector2(-9, 19) * s
    ])
    _outline(face, coat.lightened(0.12), 2.0 * s)
    _draw_eyes(c + Vector2(0, -2) * s, s, 8.0)
    draw_arc(c + Vector2(0, 5) * s, 4.5 * s, 0.25, PI - 0.25, 14, INK, 1.4 * s)
    draw_ellipse_placeholder(c + Vector2(-13, 5) * s, Vector2(4, 2) * s, Color("#D99583", 0.65))
    draw_ellipse_placeholder(c + Vector2(13, 5) * s, Vector2(4, 2) * s, Color("#D99583", 0.65))

    var leaf := PackedVector2Array([
        c + Vector2(-9, -18) * s, c + Vector2(-16, -39) * s,
        c + Vector2(1, -30) * s, c + Vector2(8, -16) * s
    ])
    _outline(leaf, SAGE.lightened(0.18), 1.8 * s)
    draw_line(c + Vector2(-11, -21) * s, c + Vector2(0, -29) * s, Color("#5D785F"), 1.1 * s)

func _draw_cinderkit(c: Vector2, s: float, coat: Color) -> void:
    var tail := PackedVector2Array([
        c + Vector2(18, 10) * s, c + Vector2(35, 4) * s,
        c + Vector2(38, -12) * s, c + Vector2(28, -19) * s,
        c + Vector2(23, -10) * s, c + Vector2(29, -5) * s,
        c + Vector2(17, 1) * s
    ])
    _outline(tail, coat.darkened(0.04), 2.2 * s)
    _outline(PackedVector2Array([
        c + Vector2(-22, 5) * s, c + Vector2(-22, -13) * s,
        c + Vector2(-12, -22) * s, c + Vector2(12, -22) * s,
        c + Vector2(23, -9) * s, c + Vector2(22, 10) * s,
        c + Vector2(12, 22) * s, c + Vector2(-12, 22) * s
    ]), coat, 2.5 * s)

    var left_ear := PackedVector2Array([
        c + Vector2(-17, -15) * s, c + Vector2(-19, -36) * s,
        c + Vector2(-3, -23) * s
    ])
    var right_ear := PackedVector2Array([
        c + Vector2(3, -23) * s, c + Vector2(19, -37) * s,
        c + Vector2(17, -13) * s
    ])
    _outline(left_ear, coat.darkened(0.06), 2.0 * s)
    _outline(right_ear, coat.darkened(0.06), 2.0 * s)
    _draw_eyes(c + Vector2(0, -3) * s, s, 8.0)
    draw_arc(c + Vector2(0, 5) * s, 5.0 * s, 0.15, PI - 0.15, 14, INK, 1.5 * s)
    draw_ellipse_placeholder(c + Vector2(-13, 5) * s, Vector2(4, 2.5) * s, Color("#E7A08A"))
    draw_ellipse_placeholder(c + Vector2(13, 5) * s, Vector2(4, 2.5) * s, Color("#E7A08A"))
    _outline(PackedVector2Array([
        c + Vector2(-5, -20) * s, c + Vector2(-9, -33) * s,
        c + Vector2(-2, -29) * s, c + Vector2(2, -41) * s,
        c + Vector2(8, -27) * s, c + Vector2(5, -18) * s
    ]), HONEY, 1.6 * s)

func _draw_puddlekin(c: Vector2, s: float, coat: Color) -> void:
    var body := PackedVector2Array([
        c + Vector2(-24, 12) * s, c + Vector2(-25, -2) * s,
        c + Vector2(-16, -17) * s, c + Vector2(0, -31) * s,
        c + Vector2(16, -17) * s, c + Vector2(25, -2) * s,
        c + Vector2(24, 12) * s, c + Vector2(13, 23) * s,
        c + Vector2(-13, 23) * s
    ])
    _outline(body, coat.lightened(0.13), 2.4 * s)
    _draw_eyes(c + Vector2(0, -4) * s, s, 8.0)
    draw_arc(c + Vector2(0, 4) * s, 4.5 * s, 0.2, PI - 0.2, 14, INK, 1.4 * s)
    draw_circle(c + Vector2(-15, -12) * s, 3.0 * s, Color("#F8F2E7", 0.75))
    draw_circle(c + Vector2(15, -2) * s, 2.0 * s, Color("#F8F2E7", 0.8))
    draw_ellipse_placeholder(c + Vector2(0, -26) * s, Vector2(18, 5) * s, SAGE)
    draw_line(c + Vector2(0, -27) * s, c + Vector2(10, -33) * s, Color("#5D785F"), 1.2 * s)
    draw_circle(c + Vector2(0, -29) * s, 3.5 * s, HONEY)

func _draw_pebbleback(c: Vector2, s: float, coat: Color) -> void:
    # A tiny mossy armadillo: low shell silhouette, pebble plates and a curious face.
    var shell := PackedVector2Array([
        c + Vector2(-29, 10) * s, c + Vector2(-27, -7) * s,
        c + Vector2(-17, -23) * s, c + Vector2(0, -28) * s,
        c + Vector2(19, -20) * s, c + Vector2(29, -3) * s,
        c + Vector2(26, 13) * s, c + Vector2(12, 21) * s,
        c + Vector2(-13, 21) * s
    ])
    _outline(shell, coat.darkened(0.06), 2.7 * s)
    for plate in range(3):
        var offset := Vector2(-12.0 + plate * 12.0, -12.0 + absf(plate - 1) * 2.0) * s
        draw_arc(c + offset, 8.0 * s, PI, TAU, 18, Color("#E0D2B9"), 1.5 * s)
    var head := PackedVector2Array([
        c + Vector2(-14, 8) * s, c + Vector2(-13, -5) * s,
        c + Vector2(-5, -14) * s, c + Vector2(8, -14) * s,
        c + Vector2(17, -5) * s, c + Vector2(17, 9) * s,
        c + Vector2(7, 17) * s, c + Vector2(-7, 16) * s
    ])
    _outline(head, coat.lightened(0.2), 1.8 * s)
    _draw_eyes(c + Vector2(2, -2) * s, s, 5.5)
    draw_circle(c + Vector2(12, 5) * s, 2.2 * s, INK)
    draw_arc(c + Vector2(-2, 5) * s, 3.5 * s, 0.15, PI - 0.15, 12, INK, 1.1 * s)

func _draw_moonmote(c: Vector2, s: float, coat: Color) -> void:
    # A sleepy moon-spirit with two soft winglets and a little star marking.
    var left_wing := PackedVector2Array([
        c + Vector2(-8, -3) * s, c + Vector2(-34, -22) * s,
        c + Vector2(-31, 2) * s, c + Vector2(-17, 17) * s
    ])
    var right_wing := PackedVector2Array([
        c + Vector2(8, -3) * s, c + Vector2(34, -22) * s,
        c + Vector2(31, 2) * s, c + Vector2(17, 17) * s
    ])
    _outline(left_wing, coat.lightened(0.1), 2.0 * s)
    _outline(right_wing, coat.lightened(0.1), 2.0 * s)
    var body := PackedVector2Array([
        c + Vector2(0, -29) * s, c + Vector2(18, -15) * s,
        c + Vector2(23, 3) * s, c + Vector2(15, 21) * s,
        c + Vector2(0, 27) * s, c + Vector2(-15, 21) * s,
        c + Vector2(-23, 3) * s, c + Vector2(-18, -15) * s
    ])
    _outline(body, coat.lightened(0.16), 2.5 * s)
    draw_arc(c + Vector2(0, -24) * s, 10.0 * s, PI + 0.2, TAU - 0.2, 20, HONEY, 2.0 * s)
    _draw_eyes(c + Vector2(0, -2) * s, s, 7.0)
    draw_arc(c + Vector2(0, 6) * s, 4.0 * s, 0.2, PI - 0.2, 12, INK, 1.2 * s)
    draw_circle(c + Vector2(-13, 8) * s, 3.0 * s, Color("#D99583", 0.55))
    draw_circle(c + Vector2(13, 8) * s, 3.0 * s, Color("#D99583", 0.55))
    draw_circle(c + Vector2(0, -14) * s, 2.2 * s, HONEY)

func _draw_breezeling(c: Vector2, s: float, coat: Color) -> void:
    # A puffin-like breeze bird with a distinct beak, feather crest and wing marks.
    var body := PackedVector2Array([
        c + Vector2(-22, 14) * s, c + Vector2(-24, -2) * s,
        c + Vector2(-15, -19) * s, c + Vector2(0, -25) * s,
        c + Vector2(17, -17) * s, c + Vector2(24, 0) * s,
        c + Vector2(19, 17) * s, c + Vector2(0, 23) * s,
        c + Vector2(-15, 20) * s
    ])
    _outline(body, coat.lightened(0.12), 2.5 * s)
    var left_wing := PackedVector2Array([
        c + Vector2(-14, -2) * s, c + Vector2(-34, -10) * s,
        c + Vector2(-27, 11) * s, c + Vector2(-12, 12) * s
    ])
    _outline(left_wing, coat.darkened(0.08), 1.8 * s)
    var beak := PackedVector2Array([
        c + Vector2(7, -1) * s, c + Vector2(23, 4) * s,
        c + Vector2(7, 9) * s
    ])
    _outline(beak, HONEY, 1.2 * s)
    _draw_eyes(c + Vector2(-3, -4) * s, s, 6.0)
    draw_arc(c + Vector2(-2, 5) * s, 3.7 * s, 0.15, PI - 0.15, 12, INK, 1.2 * s)
    var crest := PackedVector2Array([
        c + Vector2(-7, -22) * s, c + Vector2(-13, -36) * s,
        c + Vector2(-1, -30) * s, c + Vector2(8, -37) * s,
        c + Vector2(10, -20) * s
    ])
    _outline(crest, HONEY.lightened(0.05), 1.6 * s)
    draw_line(c + Vector2(-4, 12) * s, c + Vector2(6, 12) * s, Color(INK, 0.45), 1.2 * s)

func _draw_gloomling(c: Vector2, s: float, coat: Color) -> void:
    var body := PackedVector2Array([
        c + Vector2(-24, 17) * s, c + Vector2(-27, 1) * s,
        c + Vector2(-19, -15) * s, c + Vector2(-6, -23) * s,
        c + Vector2(10, -22) * s, c + Vector2(24, -11) * s,
        c + Vector2(26, 6) * s, c + Vector2(15, 21) * s,
        c + Vector2(-9, 23) * s
    ])
    _outline(body, coat, 2.4 * s)
    _outline(PackedVector2Array([
        c + Vector2(-25, -12) * s, c + Vector2(-19, -28) * s,
        c + Vector2(-5, -30) * s, c + Vector2(11, -29) * s,
        c + Vector2(25, -17) * s, c + Vector2(23, -10) * s
    ]), Color("#B88A91"), 2.0 * s)
    draw_line(c + Vector2(-17, -22) * s, c + Vector2(-20, -34) * s, INK, 2.0 * s)
    draw_line(c + Vector2(17, -22) * s, c + Vector2(20, -34) * s, INK, 2.0 * s)
    _draw_eyes(c + Vector2(0, -3) * s, s, 8.0)
    draw_arc(c + Vector2(0, 6) * s, 4.0 * s, 0.2, PI - 0.2, 14, INK, 1.3 * s)
    draw_circle(c + Vector2(-15, 9) * s, 2.5 * s, HONEY)
    draw_circle(c + Vector2(15, 9) * s, 2.5 * s, HONEY)

func _draw_boss(c: Vector2, s: float, coat: Color) -> void:
    var body := PackedVector2Array([
        c + Vector2(-34, 18) * s, c + Vector2(-31, -8) * s,
        c + Vector2(-18, -28) * s, c + Vector2(0, -34) * s,
        c + Vector2(20, -27) * s, c + Vector2(34, -6) * s,
        c + Vector2(30, 18) * s, c + Vector2(14, 30) * s,
        c + Vector2(-15, 30) * s
    ])
    _outline(body, coat.lightened(0.06), 3.2 * s)
    _outline(PackedVector2Array([
        c + Vector2(-20, -24) * s, c + Vector2(-36, -42) * s,
        c + Vector2(-14, -36) * s, c + Vector2(-5, -23) * s
    ]), SAGE.darkened(0.1), 2.4 * s)
    _outline(PackedVector2Array([
        c + Vector2(5, -23) * s, c + Vector2(15, -37) * s,
        c + Vector2(36, -43) * s, c + Vector2(20, -23) * s
    ]), SAGE.darkened(0.1), 2.4 * s)
    draw_ellipse_placeholder(c + Vector2(-10, -5) * s, Vector2(4, 5) * s, INK)
    draw_ellipse_placeholder(c + Vector2(10, -5) * s, Vector2(4, 5) * s, INK)
    draw_arc(c + Vector2(0, 9) * s, 6.0 * s, 0.1, PI - 0.1, 16, INK, 2.0 * s)
    draw_circle(c + Vector2(-20, 10) * s, 4.0 * s, Color("#D99583"))
    draw_circle(c + Vector2(20, 10) * s, 4.0 * s, Color("#D99583"))
    draw_circle(c + Vector2(0, -31) * s, 5.0 * s, HONEY)

func _draw_murkling(c: Vector2, s: float, coat: Color) -> void:
    var body := PackedVector2Array([
        c + Vector2(-25, 14) * s, c + Vector2(-22, -7) * s,
        c + Vector2(-10, -22) * s, c + Vector2(6, -25) * s,
        c + Vector2(22, -12) * s, c + Vector2(26, 7) * s,
        c + Vector2(13, 22) * s, c + Vector2(-12, 22) * s
    ])
    _outline(body, coat, 2.5 * s)
    var pebble := PackedVector2Array([
        c + Vector2(-11, -17) * s, c + Vector2(-5, -29) * s,
        c + Vector2(8, -30) * s, c + Vector2(16, -16) * s
    ])
    _outline(pebble, Color("#A79E8D"), 1.8 * s)
    _draw_eyes(c + Vector2(0, -2) * s, s, 8.0)
    draw_arc(c + Vector2(0, 6) * s, 4.0 * s, 0.15, PI - 0.15, 12, INK, 1.3 * s)
    draw_ellipse_placeholder(c + Vector2(-14, 8) * s, Vector2(4, 2) * s, Color("#C98E7C", 0.6))
    draw_ellipse_placeholder(c + Vector2(14, 8) * s, Vector2(4, 2) * s, Color("#C98E7C", 0.6))

func _draw_eyes(center: Vector2, s: float, gap: float) -> void:
    for side in [-1.0, 1.0]:
        var eye := center + Vector2(gap * side, 0) * s
        draw_ellipse_placeholder(eye, Vector2(3.2, 4.3) * s, INK)
        draw_circle(eye + Vector2(-0.9, -1.6) * s, 1.0 * s, CREAM)

func _draw_nameplate(center: Vector2, label: String, friendly: bool, s: float, health_ratio: float) -> void:
    var baseline := center.y + 48.0 * s
    draw_string(ThemeDB.fallback_font, Vector2(center.x - 54.0 * s, baseline), label, HORIZONTAL_ALIGNMENT_CENTER, 108.0 * s, 12, INK)
    var bar := Rect2(Vector2(center.x - 21.0 * s, baseline + 7.0), Vector2(42.0 * s, 4.0))
    draw_rect(bar, Color(INK, 0.18))
    draw_rect(Rect2(bar.position, Vector2(bar.size.x * clampf(health_ratio, 0.0, 1.0), bar.size.y)), SAGE if friendly else CLAY)

func _draw_plant(position: Vector2, scale_factor: float) -> void:
    var s := scale_factor
    draw_line(position, position + Vector2(0, -28) * s, SAGE.darkened(0.3), 3.0)
    draw_ellipse_placeholder(position + Vector2(-9, -22) * s, Vector2(10, 5) * s, SAGE)
    draw_ellipse_placeholder(position + Vector2(10, -29) * s, Vector2(10, 5) * s, SAGE.lightened(0.08))
    draw_circle(position + Vector2(0, -34) * s, 4.0 * s, HONEY)

func _draw_leaf_sprinkle(position: Vector2, scale_factor: float) -> void:
    var s := scale_factor
    var leaf := PackedVector2Array([
        position + Vector2(-6, 0) * s,
        position + Vector2(0, -9) * s,
        position + Vector2(8, -5) * s,
        position + Vector2(7, 4) * s,
        position + Vector2(-2, 6) * s
    ])
    _outline(leaf, Color(SAGE, 0.35), 1.1 * s)

func _draw_party_strip(size: Vector2) -> void:
    var panel := Rect2(Vector2(70, 555), Vector2(size.x - 140, 112))
    draw_rect(panel, CREAM)
    draw_rect(panel, Color(INK, 0.18), false, 1.5)
    draw_string(ThemeDB.fallback_font, Vector2(92, 580), "YOUR LITTLE PARTY", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, INK)

    var party: Array = run_snapshot.get("party", [])
    for i in range(mini(6, party.size())):
        var unit: Dictionary = party[i]
        var x := 96.0 + i * 116.0
        var unit_color := _sigil_color(str(unit.get("sigil", "leaf")))
        draw_circle(Vector2(x, 620), 11.0, unit_color)
        draw_circle(Vector2(x, 620), 11.0, INK, false, 1.2)
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
            Color(INK, 0.6)
        )

    _draw_fate_preview(Vector2(size.x - 185, 574))
    draw_string(ThemeDB.fallback_font, Vector2(size.x - 95, 671), "PREPARE  →  AUTO-BATTLE", HORIZONTAL_ALIGNMENT_RIGHT, 300, 11, INK)

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
    draw_string(ThemeDB.fallback_font, origin + Vector2(-3, 0), "FATE BOARD", HORIZONTAL_ALIGNMENT_LEFT, 110, 10, Color(INK, 0.72))
    var tile_size := 15.0
    var gap := 5.0
    for row in range(4):
        for col in range(4):
            var tile_origin := origin + Vector2(col * (tile_size + gap), 10 + row * (tile_size + gap))
            var color := fate_colors[fate_pattern[row][col]]
            draw_rect(Rect2(tile_origin, Vector2(tile_size, tile_size)), Color("#E8DECE"))
            draw_circle(tile_origin + Vector2(tile_size / 2.0, tile_size / 2.0), 4.4, color)
            draw_circle(tile_origin + Vector2(tile_size / 2.0, tile_size / 2.0), 4.4, Color(INK, 0.5), false, 1.0)

func _pixel_snap(value: float) -> float:
    return round(value / 2.0) * 2.0

func _pixel_point(point: Vector2) -> Vector2:
    return Vector2(_pixel_snap(point.x), _pixel_snap(point.y))

func _outline(points: PackedVector2Array, fill: Color, width: float = 2.2) -> void:
    var pixel_points := PackedVector2Array()
    for point in points:
        pixel_points.append(_pixel_point(point))
    draw_colored_polygon(pixel_points, fill)
    var pixel_width := maxf(2.0, round(width / 2.0) * 2.0)
    draw_polyline(_closed(pixel_points), INK, pixel_width, false)

func _closed(points: PackedVector2Array) -> PackedVector2Array:
    var result := points.duplicate()
    if points.size() > 0:
        result.append(points[0])
    return result

func draw_ellipse_placeholder(center: Vector2, radius: Vector2, color: Color) -> void:
    # Rasterise ellipses as 2-design-pixel blocks so they stay crisp after 2x upscaling.
    var rx := maxi(1, roundi(absf(radius.x) / 2.0))
    var ry := maxi(1, roundi(absf(radius.y) / 2.0))
    var snapped_center := _pixel_point(center)
    for py in range(-ry, ry + 1):
        for px in range(-rx, rx + 1):
            var nx := float(px * px) / float(rx * rx)
            var ny := float(py * py) / float(ry * ry)
            if nx + ny <= 1.0:
                var pixel_origin := snapped_center + Vector2(px * 2.0, py * 2.0)
                draw_rect(Rect2(pixel_origin, Vector2(2, 2)), color)
