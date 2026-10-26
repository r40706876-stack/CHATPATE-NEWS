extends Node2D
# Godot 4 Movie Maker mode: deterministic cartoon parcel shot.
var frame_no := 0
func _process(_delta):
    queue_redraw()
    frame_no += 1
    if frame_no >= 90: get_tree().quit()
func _draw():
    var t := float(frame_no)/30.0
    draw_rect(Rect2(0,0,720,1280),Color("#f6e9ce"))
    draw_rect(Rect2(50,760,620,220),Color("#bd8255"))
    var lift := maxf(0.0, minf(1.0,(t-0.7)*2.0))*260.0
    draw_rect(Rect2(210,760-lift,300,230),Color("#315c8b"))
    draw_rect(Rect2(235,790-lift,250,150),Color("#a9dce8"))
    draw_rect(Rect2(190,900,340,230),Color("#c28b52"))
    draw_line(Vector2(360,900),Vector2(360,1130),Color("#f2d39b"),28)
