"""
Generator syntetycznych danych treningowych (Listing 1 z raportu).
Uzupełniono o brakujące wzorce L, P, X.
"""
import numpy as np

# Bazowe wzorce znaków nawigacyjnych 8x8
# N - strzałka w górę (z raportu)
# L, P, X - dodane, żeby całość się kompilowała
BASE_PATTERNS = {
    'N': np.array([  # strzałka w górę
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.uint8),

    'L': np.array([  # strzałka w lewo
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.uint8),

    'P': np.array([  # strzałka w prawo (lustrzane odbicie L)
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]], dtype=np.uint8),

    'X': np.array([  # znak X - zawróć
        [1, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 1]], dtype=np.uint8),
}

# Mapowanie etykieta -> indeks klasy (zgodne z raportem: 00=N, 01=L, 10=P, 11=X)
LABEL_TO_IDX = {'N': 0, 'L': 1, 'P': 2, 'X': 3}
IDX_TO_LABEL = {v: k for k, v in LABEL_TO_IDX.items()}
NUM_CLASSES = 4


def generate_sample(label, noise=0.05, max_shift=2):
    """
    Zwraca macierz 8x8 z dodanymi zaburzeniami.
    (Listing 1 z raportu)
    """
    img = BASE_PATTERNS[label].copy()
    # translacja o losową liczbę pikseli
    dx = np.random.randint(-max_shift, max_shift + 1)
    dy = np.random.randint(-max_shift, max_shift + 1)
    img = np.roll(img, (dy, dx), axis=(0, 1))
    # szum typu salt-and-pepper
    mask = np.random.random(img.shape) < noise
    img[mask] = 1 - img[mask]
    return img


def generate_dataset(n_per_class=500, noise=0.05, max_shift=2, seed=None):
    """Generuje zbiór danych: (X, y) gdzie X ma kształt (N, 64), y ma kształt (N,)."""
    if seed is not None:
        np.random.seed(seed)

    images = []
    labels = []
    for label, idx in LABEL_TO_IDX.items():
        for _ in range(n_per_class):
            img = generate_sample(label, noise=noise, max_shift=max_shift)
            images.append(img)
            labels.append(idx)

    X = np.stack(images).astype(np.float32)  # (N, 8, 8)
    y = np.array(labels, dtype=np.int64)

    # mieszamy
    perm = np.random.permutation(len(y))
    return X[perm], y[perm]


if __name__ == "__main__":
    # Szybki sanity check
    X, y = generate_dataset(n_per_class=5, seed=42)
    print(f"Kształt X: {X.shape}, kształt y: {y.shape}")
    print(f"Rozkład klas: {np.bincount(y)}")
    print(f"\nPrzykładowy obraz (klasa {IDX_TO_LABEL[y[0]]}):")
    print(X[0].astype(int))
