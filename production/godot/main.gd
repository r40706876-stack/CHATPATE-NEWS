extends Node2D
# Three-second, continuously animated COD-showroom insert for Bakra News.
# No external image or font assets: reproducible on the headless runner.
var frame_no := 0

func _process(_delta: float) -> void:
    frame_no += 1
    queue_redraw()
    if frame_no >= 90:
        get_tree().quit()

func _parcel(x: float, y: float, w: float, h: float, shade: Color) -> void:
    draw_rect(Rect2(x + 7, y + 9, w, h), Color(0.18, 0.15, 0.15, 0.22))
    draw_rect(Rect2(x, y, w, h), shade)
    draw_rect(Rect2(x + w * 0.44, y, w * 0.12, h), Color("#ffe0a0"))
    draw_line(Vector2(x, y), Vector2(x + w, y), Color("#704725"), 4.0)
    draw_line(Vector2(x, y + h), Vector2(x + w, y + h), Color("#704725"), 3.0)

func _courier(t: float) -> void:
    var bounce := sin(t * 10.0) * 5.0
    # Delivery worker on the left: head, surprised eyes, moving arm.
    draw_rect(Rect2(65, 870 + bounce, 112, 215), Color("#315f91"))
    draw_circle(Vector2(121, 818 + bounce), 61, Color("#f0b882"))
    draw_rect(Rect2(72, 754 + bounce, 96, 28), Color("#27374f"))
    draw_circle(Vector2(101, 815 + bounce), 6, Color("#22283c"))
    draw_circle(Vector2(145, 815 + bounce), 6, Color("#22283c"))
    draw_circle(Vector2(124, 847 + bounce), 13, Color("#613e39"))
    draw_line(Vector2(169, 910 + bounce), Vector2(218 + sin(t * 8.0) * 18.0, 850 + bounce), Color("#f0b882"), 22.0)
    draw_rect(Rect2(207 + sin(t * 8.0) * 18.0, 812 + bounce, 82, 65), Color("#fff6df"))
    draw_string(ThemeDB.fallback_font, Vector2(216 + sin(t * 8.0) * 18.0, 855 + bounce), "COD", HORIZONTAL_ALIGNMENT_LEFT, -1, 25, Color("#e44343"))

func _draw() -> void:
    var t: float = float(frame_no) / 30.0
    var pulse: float = sin(t * 9.0)
    # Warm news-studio showroom, layered walls and ground.
    draw_rect(Rect2(0, 0, 720, 1280), Color("#f8e9ce"))
    draw_rect(Rect2(0, 0, 720, 185), Color("#f9d66f"))
    draw_rect(Rect2(0, 190, 720, 17), Color("#d84c3e"))
    draw_rect(Rect2(0, 1080, 720, 200), Color("#d2b58e"))
    draw_rect(Rect2(28, 255, 664, 760), Color("#fff5df"))
    draw_rect(Rect2(44, 270, 632, 730), Color("#c8e7e6"))
    # Animated speed stripes emphasize parcels arriving.
    for i in range(4):
        var sx: float = fposmod(t * 270.0 + i * 205.0, 980.0) - 140.0
        draw_line(Vector2(sx, 332 + i * 82), Vector2(sx + 75, 332 + i * 82), Color("#fffdf4"), 11.0)
    draw_string(ThemeDB.fallback_font, Vector2(360, 105), "SWEETS?  TV DELIVERY!", HORIZONTAL_ALIGNMENT_CENTER, 680, 43, Color("#292f51"))
    draw_string(ThemeDB.fallback_font, Vector2(360, 162), "BAKRA NEWS  |  COD SHOCK", HORIZONTAL_ALIGNMENT_CENTER, 680, 26, Color("#b23430"))

    # TV slides into the doorway, then keeps bobbing throughout the shot.
    var arrive: float = clampf((t - 0.08) / 0.75, 0.0, 1.0)
    var tv_x: float = -440.0 + 620.0 * (1.0 - pow(1.0 - arrive, 3.0))
    var tv_y: float = 420.0 + sin(t * 7.0) * 14.0
    draw_rect(Rect2(tv_x + 13, tv_y + 14, 376, 276), Color(0.1, 0.15, 0.21, 0.24))
    draw_rect(Rect2(tv_x, tv_y, 376, 260), Color("#29364e"))
    draw_rect(Rect2(tv_x + 22, tv_y + 22, 332, 207), Color("#4ebad0"))
    draw_rect(Rect2(tv_x + 34, tv_y + 35, 306, 175), Color("#7bd2dc"))
    draw_circle(Vector2(tv_x + 190 + sin(t * 5.0) * 34.0, tv_y + 125), 47 + pulse * 5.0, Color("#ffcb51"))
    draw_rect(Rect2(tv_x + 166, tv_y + 260, 45, 65), Color("#29364e"))
    draw_rect(Rect2(tv_x + 104, tv_y + 316, 172, 15), Color("#29364e"))
    draw_string(ThemeDB.fallback_font, Vector2(tv_x + 190, tv_y + 191), "4K TV", HORIZONTAL_ALIGNMENT_CENTER, 270, 44, Color("#253a55"))

    # Parcels cascade from the right; their bounce never becomes a frozen card.
    var box_arrive: float = clampf((t - 0.45) / 0.7, 0.0, 1.0)
    var bx: float = 835.0 - 355.0 * box_arrive
    _parcel(bx, 835.0 + sin(t * 8.0) * 7.0, 175, 140, Color("#cb925a"))
    _parcel(bx - 40, 695.0 + sin(t * 7.0 + 1.0) * 9.0, 185, 134, Color("#dfac6c"))
    _parcel(bx + 16, 563.0 + sin(t * 9.0 + 2.0) * 9.0, 140, 120, Color("#b8794c"))
    _courier(t)

    # COD invoice pops into view, pulses and moves until the last frame.
    if t > 1.0:
        var pop: float = clampf((t - 1.0) * 2.5, 0.0, 1.0)
        var yy: float = 1100.0 - 145.0 * pop + sin(t * 7.0) * 6.0
        draw_rect(Rect2(270, yy, 390, 135), Color("#fff9ed"))
        draw_rect(Rect2(270, yy + 95, 390, 40), Color("#d73d3d"))
        draw_string(ThemeDB.fallback_font, Vector2(465, yy + 55), "CASH ON DELIVERY", HORIZONTAL_ALIGNMENT_CENTER, 370, 27, Color("#28314b"))
        draw_string(ThemeDB.fallback_font, Vector2(465, yy + 126), "1.69 LAKH!", HORIZONTAL_ALIGNMENT_CENTER, 370, 33, Color("#ffffff"))
    # Comic emphasis flashes, not a still image.
    for i in range(6):
        var angle: float = float(i) * TAU / 6.0 + t * 1.2
        var center: Vector2 = Vector2(355, 365)
        var p1: Vector2 = center + Vector2(cos(angle), sin(angle)) * (60.0 + pulse * 4.0)
        var p2: Vector2 = center + Vector2(cos(angle), sin(angle)) * 91.0
        draw_line(p1, p2, Color("#f3a531"), 7.0)
