"""
Layer 1 - ekstrakcja cech (Listing 2 z raportu).
19 cech: 8 projekcji wierszy + 8 projekcji kolumn + środek masy (x,y) + suma pikseli.
"""
import numpy as np


def extract_features(img):
    """Zwraca 19-elementowy wektor cech z obrazu 8x8."""
    row_proj = img.sum(axis=1)            # 8 wartości
    col_proj = img.sum(axis=0)            # 8 wartości
    total = img.sum()                     # 1 wartość
    # środek masy (unikamy dzielenia przez zero)
    if total > 0:
        ys, xs = np.nonzero(img)
        cm_y = ys.mean()
        cm_x = xs.mean()
    else:
        cm_y, cm_x = 3.5, 3.5             # środek matrycy
    features = np.concatenate([
        row_proj, col_proj,
        [cm_x, cm_y, total]
    ])
    return features.astype(np.float32)


def extract_features_batch(images):
    """Ekstrakcja cech dla całego batcha obrazów."""
    return np.stack([extract_features(img) for img in images])


NUM_FEATURES = 19


if __name__ == "__main__":
    from data_generator import generate_sample
    img = generate_sample('N', noise=0.0, max_shift=0)
    feats = extract_features(img)
    print(f"Liczba cech: {len(feats)}")
    print(f"Wektor cech: {feats}")
