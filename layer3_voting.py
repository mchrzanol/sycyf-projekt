"""
Layer 3 - głosowanie większościowe (Listing 4 z raportu).
"""
import numpy as np


def majority_vote(predictions):
    """
    predictions: lista 6 etykiet klas (0..3).
    W razie remisu - klasa o wyższym indeksie (jak w HDL).
    """
    assert len(predictions) == 6
    counts = [0, 0, 0, 0]
    for p in predictions:
        counts[p] += 1
    # wybieramy klasę z największą liczbą głosów
    # w razie remisu - klasa o wyższym indeksie
    best = 0
    for i in range(1, 4):
        if counts[i] >= counts[best]:
            best = i
    return best


def voted_accuracy(model_predictions, true_labels, window=6):
    """
    Liczy dokładność po zastosowaniu głosowania na oknach po `window` klatek.
    Zakładamy, że sąsiednie klatki w tablicy mają tę samą prawdziwą klasę
    (grupujemy po `window` próbek).
    """
    n = len(model_predictions) // window * window
    preds = np.array(model_predictions[:n]).reshape(-1, window)
    trues = np.array(true_labels[:n]).reshape(-1, window)

    voted = np.array([majority_vote(list(row)) for row in preds])
    # prawdziwa klasa okna - większość w prawdziwych etykietach
    true_voted = np.array([majority_vote(list(row)) for row in trues])
    return float((voted == true_voted).mean())


if __name__ == "__main__":
    # test: 4 głosy na klasę 0, 1 na klasę 1, 1 na klasę 2
    print(majority_vote([0, 0, 0, 0, 1, 2]))  # powinno być 0
    # test: remis 3-3 -> wyższy indeks
    print(majority_vote([0, 0, 0, 1, 1, 1]))  # powinno być 1
