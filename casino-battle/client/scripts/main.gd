extends Node2D

const PAPER := Color("#F3EBDD")
const PAPER_SHADE := Color("#E7D9C2")
const INK := Color("#4A4540")
const SAGE := Color("#91A68A")
const CLAY := Color("#C77F62")
const HONEY := Color("#DDBB72")
const BLUE := Color("#8FAEBC")
const BERRY := Color("#9C7180")

var elapsed := 0.0

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

func _draw_battlefield(size: Vector2) -> void:
    var arena := Rect2(Vector2(70, 120), Vector2(size.x - 140, 400))
    draw_rect(arena, Color("#E9E0CF"))
    draw_rect(arena, Color(INK, 0.22), false, 2.0)

    for i in range(11):
        var x := arena.position.x + 24 + i * ((arena.size.x - 48) / 10.0)
        draw_line(Vector2(x, arena.position.y + 22), Vector2(x, arena.end.y - 22), Color(INK, 0.055), 1.0)

    for i in range(5):
        var y := arena.position.y + 24 + i * ((arena.size.y - 48) / 4.0)
        draw_line(Vector2(arena.position.x + 22, y), Vector2(arena.end.x - 22, y), Color(INK, 0.055), 1.0)

    _draw_plant(Vector2(145, 450), 1.0)
    _draw_plant(Vector2(1100, 185), 0.8)
    _draw_creature(Vector2(330, 330), SAGE, "Mossguard", true, 1.0)
    _draw_creature(Vector2(470, 285), CLAY, "Cinderkit", true, 0.88)
    _draw_creature(Vector2(560, 380), BLUE, "Puddlekin", true, 0.95)
    _draw_creature(Vector2(860, 310), BERRY, "Gloomling", false, 1.0)
    _draw_creature(Vector2(990, 390), Color("#8D8578"), "Murkling", false, 0.88)

    var bob := sin(elapsed * 2.1) * 3.0
    draw_arc(Vector2(330, 360 + bob), 33.0, 0.0, TAU, 48, Color(HONEY, 0.65), 2.0)
    draw_circle(Vector2(860, 345), 34.0, Color(CLAY, 0.09))

func _draw_creature(center: Vector2, coat: Color, label: String, friendly: bool, scale_factor: float) -> void:
    var bob := sin(elapsed * 2.5 + center.x * 0.01) * 2.5
    var c := center + Vector2(0, bob)
    var s := scale_factor
    var body := PackedVector2Array([
        c + Vector2(-24, 13) * s,
        c + Vector2(-23, -10) * s,
        c + Vector2(-12, -24) * s,
        c + Vector2(9, -27) * s,
        c + Vector2(25, -12) * s,
        c + Vector2(23, 12) * s,
        c + Vector2(12, 24) * s,
        c + Vector2(-12, 24) * s
    ])
    draw_colored_polygon(body, coat)
    draw_polyline(_closed(body), INK, 2.3, true)
    draw_ellipse_placeholder(c + Vector2(-9, -5) * s, Vector2(3.0, 4.0) * s, INK)
    draw_ellipse_placeholder(c + Vector2(9, -5) * s, Vector2(3.0, 4.0) * s, INK)
    draw_arc(c + Vector2(0, 3) * s, 5.0 * s, 0.2, PI - 0.2, 16, INK, 1.7)
    if friendly:
        draw_colored_polygon(PackedVector2Array([
            c + Vector2(-13, -22) * s, c + Vector2(-5, -42) * s,
            c + Vector2(3, -21) * s
        ]), SAGE.darkened(0.08))
    else:
        draw_circle(c + Vector2(0, -31) * s, 5.0 * s, HONEY)
    draw_string(ThemeDB.fallback_font, c + Vector2(-44, 48) * s, label, HORIZONTAL_ALIGNMENT_CENTER, 88, 12, INK)

func _draw_plant(position: Vector2, scale_factor: float) -> void:
    var s := scale_factor
    draw_line(position, position + Vector2(0, -28) * s, SAGE.darkened(0.3), 3.0)
    draw_ellipse_placeholder(position + Vector2(-9, -22) * s, Vector2(10, 5) * s, SAGE)
    draw_ellipse_placeholder(position + Vector2(10, -29) * s, Vector2(10, 5) * s, SAGE.lightened(0.08))
    draw_circle(position + Vector2(0, -34) * s, 4.0 * s, HONEY)

func _draw_party_strip(size: Vector2) -> void:
    var panel := Rect2(Vector2(70, 555), Vector2(size.x - 140, 112))
    draw_rect(panel, Color("#F8F2E7"))
    draw_rect(panel, Color(INK, 0.18), false, 1.5)
    draw_string(ThemeDB.fallback_font, Vector2(92, 580), "YOUR LITTLE PARTY", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, INK)
    var labels := ["Mossguard · Guardian", "Cinderkit · Striker", "Puddlekin · Support"]
    var colors := [SAGE, CLAY, BLUE]
    for i in range(labels.size()):
        var x := 100.0 + i * 275.0
        draw_circle(Vector2(x, 620), 13.0, colors[i])
        draw_circle(Vector2(x, 620), 13.0, INK)
        draw_string(ThemeDB.fallback_font, Vector2(x + 25, 625), labels[i], HORIZONTAL_ALIGNMENT_LEFT, 230, 13, INK)
    draw_string(ThemeDB.fallback_font, Vector2(size.x - 95, 625), "PREPARE  →  AUTO-BATTLE", HORIZONTAL_ALIGNMENT_RIGHT, 300, 13, INK)

func _closed(points: PackedVector2Array) -> PackedVector2Array:
    var result := points.duplicate()
    if points.size() > 0:
        result.append(points[0])
    return result

func draw_ellipse_placeholder(center: Vector2, radius: Vector2, color: Color) -> void:
    draw_set_transform(center, 0.0, radius)
    draw_circle(Vector2.ZERO, 1.0, color)
    draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
