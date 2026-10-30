"""एक photo से चेहरे के भाव (30 Oct, मालिक: "Blender से realistic सब emotion") — असली photo ही चलती है,
सिर्फ़ भौंह/पलक/होंठ के कोने/गाल की जगह खिसकती है (Blender में photo वाली mesh की shape keys, यहाँ वही हिसाब).
blender_face.py यही HANDLES पढ़कर mesh के vertex हिलाता है; preview() बिना Blender वही नतीजा (जाँच के लिए).

landmarks असली photo (assets/real/ramesh.png, 1145x1374) के pixel हैं.
"""
import math

SIZE = (1145, 1374)
P = {   # (x, y)
    "eye_l": (500, 311), "eye_r": (625, 311),
    "lid_up_l": (500, 292), "lid_up_r": (625, 292), "lid_lo_l": (500, 329), "lid_lo_r": (625, 329),
    "brow_in_l": (540, 272), "brow_mid_l": (495, 265), "brow_out_l": (452, 272),
    "brow_in_r": (585, 272), "brow_mid_r": (632, 265), "brow_out_r": (678, 272),
    "mouth_l": (512, 422), "mouth_r": (628, 422), "lip_lo": (570, 438), "jaw": (570, 495),
    "cheek_l": (468, 385), "cheek_r": (662, 385),
}

# भाव → [(landmark, dx, dy, sigma)]
HANDLES = {
    "hasi": [("mouth_l", -9, -16, 24), ("mouth_r", 9, -16, 24), ("cheek_l", 0, -10, 32), ("cheek_r", 0, -10, 32),
             ("lid_lo_l", 0, -5, 13), ("lid_lo_r", 0, -5, 13), ("brow_mid_l", 0, -4, 30), ("brow_mid_r", 0, -4, 30)],
    "hairan": [("brow_mid_l", 0, -18, 34), ("brow_mid_r", 0, -18, 34), ("lid_up_l", 0, -3, 9), ("lid_up_r", 0, -3, 9),
               ("jaw", 0, 10, 42), ("lip_lo", 0, 5, 16),
               ("mouth_l", 3, 0, 16), ("mouth_r", -3, 0, 16)],
    "gussa": [("brow_in_l", 8, 15, 20), ("brow_in_r", -8, 15, 20), ("brow_out_l", 0, -4, 18), ("brow_out_r", 0, -4, 18),
              ("lid_up_l", 0, 6, 12), ("lid_up_r", 0, 6, 12), ("mouth_l", 2, 8, 18), ("mouth_r", -2, 8, 18)],
    "udaas": [("brow_in_l", 0, -10, 16), ("brow_in_r", 0, -10, 16), ("brow_out_l", 0, 6, 18), ("brow_out_r", 0, 6, 18),
              ("lid_up_l", 0, 4, 12), ("lid_up_r", 0, 4, 12), ("mouth_l", 0, 10, 20), ("mouth_r", 0, 10, 20)],
    "tanz": [("brow_mid_r", 0, -20, 32), ("brow_in_l", 0, 6, 20), ("mouth_r", 8, -14, 22), ("mouth_l", 0, 3, 16),
             ("lid_lo_l", 0, -5, 12), ("lid_up_l", 0, 4, 11)],
}


def disp(expr, x, y, k=1.0):
    """(x, y) पर कितना खिसके — handles का gaussian जोड़."""
    dx = dy = 0.0
    for name, hx, hy, s in HANDLES[expr]:
        px, py = P[name]
        w = math.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * s * s))
        dx += hx * w * k
        dy += hy * w * k
    return dx, dy


def preview(src, out_dir, k=1.0):
    """बिना Blender: वही खिसकाव (उल्टा नक्शा) — Blender के नतीजे से पहले देखने के लिए."""
    from pathlib import Path

    import cv2
    import numpy as np
    im = cv2.imread(str(src))
    h, w = im.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for expr in HANDLES:
        dx = np.zeros((h, w), np.float32)
        dy = np.zeros((h, w), np.float32)
        for name, hx, hy, s in HANDLES[expr]:
            px, py = P[name]
            g = np.exp(-((xs - px) ** 2 + (ys - py) ** 2) / (2 * s * s)).astype(np.float32)
            dx += hx * g * k
            dy += hy * g * k
        cv2.imwrite(str(out / f"{expr}.png"), cv2.remap(im, xs - dx, ys - dy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT))


if __name__ == "__main__":
    import sys
    preview(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
