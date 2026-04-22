"""
Główny skrypt - trening i ewaluacja całego pipeline'u.
Odtwarza Testy 1, 2 i 3 z rozdziału "Scenariusze testowe i wyniki" raportu.
"""
import numpy as np

from data_generator import generate_dataset, generate_sample, LABEL_TO_IDX, IDX_TO_LABEL, NUM_CLASSES
from layer1_features import extract_features_batch, NUM_FEATURES
from layer2_mlp import SignMLP, train_mlp
from layer3_voting import majority_vote


def build_dataset(n_per_class, noise, max_shift, seed):
    """Generuje zbiór i od razu wyciąga cechy (Layer 1)."""
    X_img, y = generate_dataset(n_per_class=n_per_class,
                                noise=noise, max_shift=max_shift, seed=seed)
    X_feat = extract_features_batch(X_img)
    return X_img, X_feat, y


def test1_confusion_matrix(model, X_feat, y):
    """Test 1 - dokładność i macierz pomyłek na pojedynczych klatkach."""
    pred = model.classify(X_feat)
    acc = float((pred == y).mean())
    # macierz pomyłek
    cm = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=np.int32)
    for t, p in zip(y, pred):
        cm[t, p] += 1
    # normalizacja po wierszach (procenty)
    cm_pct = cm / cm.sum(axis=1, keepdims=True) * 100
    return acc, cm, cm_pct


def test2_robustness(model, noise_levels, shift_levels, n_per_class=100, seed=999):
    """Test 2 - degradacja przy rosnącym szumie i translacjach."""
    results = {'noise': [], 'shift': []}
    for ns in noise_levels:
        _, Xf, y = build_dataset(n_per_class, noise=ns, max_shift=2, seed=seed)
        pred = model.classify(Xf)
        results['noise'].append((ns, float((pred == y).mean())))
    for sh in shift_levels:
        _, Xf, y = build_dataset(n_per_class, noise=0.05, max_shift=sh, seed=seed)
        pred = model.classify(Xf)
        results['shift'].append((sh, float((pred == y).mean())))
    return results


def test3_voting_gain(model, noise_levels, n_per_class=100, window=6, seed=777):
    """Test 3 - porównanie z/bez Layer 3 dla różnych poziomów szumu."""
    results = []
    for ns in noise_levels:
        # Dla każdej klasy generujemy n_per_class*window klatek,
        # tak żeby dało się zrobić n_per_class "okien decyzyjnych" po window klatek,
        # w których prawdziwa klasa jest stała.
        np.random.seed(seed + int(ns * 1000))
        all_preds_single = []
        all_preds_voted = []
        all_true = []
        for label, idx in LABEL_TO_IDX.items():
            for _ in range(n_per_class):
                # okno window klatek tej samej klasy
                window_imgs = [generate_sample(label, noise=ns, max_shift=2)
                               for _ in range(window)]
                feats = extract_features_batch(np.stack(window_imgs))
                window_preds = model.classify(feats)
                # bez głosowania: każda klatka osobno
                all_preds_single.extend(list(window_preds))
                all_true.extend([idx] * window)
                # z głosowaniem: jedna decyzja na okno
                voted = majority_vote(list(window_preds))
                all_preds_voted.append(voted)

        single_acc = float((np.array(all_preds_single) == np.array(all_true)).mean())
        # dla wersji z głosowaniem prawdziwą etykietą okna jest ta sama klasa
        voted_true = np.repeat(
            np.array([LABEL_TO_IDX[l] for l in LABEL_TO_IDX.keys()]),
            n_per_class
        )
        voted_acc = float((np.array(all_preds_voted) == voted_true).mean())
        results.append((ns, single_acc, voted_acc))
    return results


def main():
    print("=" * 60)
    print("SYCYF - Projekt Ostatni Strażnik Pustki")
    print("Model referencyjny w Pythonie")
    print("=" * 60)

    # 1. Dane treningowe i walidacyjne
    print("\n[1] Generowanie danych...")
    _, X_tr, y_tr = build_dataset(n_per_class=500, noise=0.05, max_shift=2, seed=42)
    _, X_val, y_val = build_dataset(n_per_class=100, noise=0.05, max_shift=2, seed=123)
    print(f"  Train: {X_tr.shape}, Val: {X_val.shape}")
    print(f"  Liczba cech (Layer 1): {NUM_FEATURES}")

    # 2. Trening MLP (Layer 2)
    print("\n[2] Trenuję MLP...")
    model = SignMLP(n_in=NUM_FEATURES, n_hidden=24, n_out=NUM_CLASSES, seed=42)
    train_mlp(model, X_tr, y_tr, X_val, y_val,
              epochs=80, batch_size=32, lr=0.1, lr_decay=0.97, verbose=True)
    model.save('weights.npz')
    print("  Wagi zapisane do weights.npz")

    # 3. Test 1 - macierz pomyłek
    print("\n[3] Test 1 - dokładność bazowa i macierz pomyłek")
    _, X_test, y_test = build_dataset(n_per_class=100, noise=0.05, max_shift=2, seed=2026)
    acc, cm, cm_pct = test1_confusion_matrix(model, X_test, y_test)
    print(f"  Dokładność: {acc*100:.2f}%")
    print("  Macierz pomyłek (wiersze=prawda, kolumny=predykcja, wartości w %):")
    print(f"      {'N':>6} {'L':>6} {'P':>6} {'X':>6}")
    for i in range(NUM_CLASSES):
        row = "  " + IDX_TO_LABEL[i] + " "
        for j in range(NUM_CLASSES):
            row += f"{cm_pct[i,j]:6.1f}"
        print(row)

    # 4. Test 2 - odporność na szum i translacje
    print("\n[4] Test 2 - odporność")
    rob = test2_robustness(model,
                           noise_levels=[0.0, 0.05, 0.10, 0.15, 0.20],
                           shift_levels=[0, 1, 2, 3, 4])
    print("  Szum:")
    for ns, a in rob['noise']:
        print(f"    {ns*100:5.1f}%  ->  {a*100:6.2f}%")
    print("  Translacja:")
    for sh, a in rob['shift']:
        print(f"    +/-{sh} px ->  {a*100:6.2f}%")

    # 5. Test 3 - rola głosowania
    print("\n[5] Test 3 - zysk z głosowania (Layer 3)")
    vr = test3_voting_gain(model, noise_levels=[0.05, 0.10, 0.15])
    print(f"  {'Szum':>6} {'bez Layer3':>12} {'z Layer3':>12} {'zysk':>10}")
    for ns, s, v in vr:
        print(f"  {ns*100:5.1f}%  {s*100:11.2f}%  {v*100:11.2f}%  {(v-s)*100:+8.2f} p.p.")

    print("\n" + "=" * 60)
    print("Gotowe.")
    print("=" * 60)


if __name__ == "__main__":
    main()
