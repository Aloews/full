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

var fate_pattern := [
    [0, 1, 0, 3],
    [2, 1, 4, 3],
    [2, 5, 4, 0],
    [3, 5, 2, 1]
]
var fate_colors := [SAGE, CLAY, BLUE, Color("#A99B82"), BERRY, HONEY]

func _ready() -> void:
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
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
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
            _refresh_run()
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

func _on_draw_pressed() -> void:
    if run_id.is_empty():
        return
    _send_request("draw", HTTPClient.METHOD_POST, "/api/v1/runs/%s/draw" % run_id, "{}")

func _on_battle_pressed() -> void:
    if run_id.is_empty():
        return
    _send_request("battle", HTTPClient.METHOD_POST, "/api/v1/runs/%s/battle" % run_id, "{}")

func _update_controls() -> void:
    if not is_instance_valid(draw_button):
        return
    var active := str(run_snapshot.get("phase", "preparation")) == "preparation"
    var essence := int(run_snapshot.get("essence", 0))
    draw_button.disabled = api_busy or run_id.is_empty() or not active or essence <= 0
    battle_button.disabled = api_busy or run_id.is_empty() or not active or run_snapshot.get("party", []).is_empty()
    status_label.text = status_text

func _process(delta: float) -> void:
    elapsed += delta
    queue_redraw()

func _draw() -> void:
    var size := get_viewport_rect().size
    draw_rect(Rect2(Vector2.ZERO, size), PAPER)
    _draw_paper_grain(size)
    _draw_header()
    _draw_battlefield(size)
    _draw_party_strip(size)

func _draw_paper_grain(size: Vector2) -> void:
    for i in range(90):
        var x := fmod(float(i * 137 + 41), size.x)
        var y := fmod(float(i * 71 + 19), size.y)
        draw_line(Vector2(x, y), Vector2(x + 2.0, y + 1.0), Color(0.35, 0.29, 0.22, 0.045), 1.0)

func _draw_header() -> void:
    draw_string(ThemeDB.fallback_font, Vector2(48, 52), "THE MOSS MEADOW", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, INK)
    draw_string(ThemeDB.fallback_font, Vector2(48, 80), "A little party, a very big adventure", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(INK, 0.65))
    draw_string(ThemeDB.fallback_font, Vector2(1120, 52), "WAVE 01", HORIZONTAL_ALIGNMENT_RIGHT, 180, 17, INK)
    draw_string(ThemeDB.fallback_font, Vector2(1120, 78), "♥  ♥  ♥", HORIZONTAL_ALIGNMENT_RIGHT, 180, 15, CLAY)

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

    _draw_plant(Vector2(145, 450), 1.0)
    _draw_plant(Vector2(1100, 185), 0.8)
    _draw_plant(Vector2(720, 470), 0.55)
    _draw_creature(Vector2(330, 330), SAGE, "Mossguard", true, 1.0)
    _draw_creature(Vector2(470, 285), CLAY, "Cinderkit", true, 0.88)
    _draw_creature(Vector2(560, 380), BLUE, "Puddlekin", true, 0.95)
    _draw_creature(Vector2(860, 310), BERRY, "Gloomling", false, 1.0)
    _draw_creature(Vector2(990, 390), Color("#8D8578"), "Murkling", false, 0.88)

    var bob := sin(elapsed * 2.1) * 3.0
    draw_arc(Vector2(330, 360 + bob), 37.0, 0.0, TAU, 48, Color(HONEY, 0.48), 2.0)
    draw_circle(Vector2(860, 345), 34.0, Color(CLAY, 0.07))
    _draw_leaf_sprinkle(Vector2(250, 210), 0.7)
    _draw_leaf_sprinkle(Vector2(1060, 465), 0.55)

func _draw_creature(center: Vector2, coat: Color, label: String, friendly: bool, scale_factor: float) -> void:
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
        "Gloomling":
            _draw_gloomling(c, s, coat)
        _:
            _draw_murkling(c, s, coat)

    _draw_nameplate(c, label, friendly, s)

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

func _draw_nameplate(center: Vector2, label: String, friendly: bool, s: float) -> void:
    var baseline := center.y + 48.0 * s
    draw_string(ThemeDB.fallback_font, Vector2(center.x - 54.0 * s, baseline), label, HORIZONTAL_ALIGNMENT_CENTER, 108.0 * s, 12, INK)
    var bar := Rect2(Vector2(center.x - 21.0 * s, baseline + 7.0), Vector2(42.0 * s, 4.0))
    draw_rect(bar, Color(INK, 0.18))
    draw_rect(Rect2(bar.position, Vector2(bar.size.x * (0.82 if friendly else 0.58), bar.size.y)), SAGE if friendly else CLAY)

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

    var labels := ["Mossguard  ·  Guardian", "Cinderkit  ·  Striker", "Puddlekin  ·  Support"]
    var colors := [SAGE, CLAY, BLUE]
    for i in range(labels.size()):
        var x := 100.0 + i * 275.0
        draw_circle(Vector2(x, 620), 13.0, colors[i])
        draw_circle(Vector2(x, 620), 13.0, INK)
        draw_string(ThemeDB.fallback_font, Vector2(x + 25, 625), labels[i], HORIZONTAL_ALIGNMENT_LEFT, 230, 13, INK)

    _draw_fate_preview(Vector2(size.x - 185, 574))
    draw_string(ThemeDB.fallback_font, Vector2(size.x - 95, 671), "PREPARE  →  AUTO-BATTLE", HORIZONTAL_ALIGNMENT_RIGHT, 300, 11, INK)

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

func _outline(points: PackedVector2Array, fill: Color, width: float = 2.2) -> void:
    draw_colored_polygon(points, fill)
    draw_polyline(_closed(points), INK, width, true)
    var pencil_points := PackedVector2Array()
    for point in points:
        pencil_points.append(point + Vector2(1.0, 0.7))
    draw_polyline(_closed(pencil_points), Color(INK, 0.2), maxf(0.7, width * 0.35), true)

func _closed(points: PackedVector2Array) -> PackedVector2Array:
    var result := points.duplicate()
    if points.size() > 0:
        result.append(points[0])
    return result

func draw_ellipse_placeholder(center: Vector2, radius: Vector2, color: Color) -> void:
    draw_set_transform(center, 0.0, radius)
    draw_circle(Vector2.ZERO, 1.0, color)
    draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
