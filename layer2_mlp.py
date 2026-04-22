"""
Layer 2 - klasyfikator MLP (Listing 3 z raportu).
Ręczna implementacja bez sklearn/torch - wg wytycznych z raportu,
żeby dało się przenieść do Veriloga.

Architektura: 19 -> 16 (ReLU) -> 4 (logits).
Trening: minibatch SGD + cross-entropy, wszystko na NumPy.
"""
import numpy as np


class SignMLP:
    """MLP z jedną warstwą ukrytą. Listing 3 z raportu."""

    def __init__(self, weights_file=None, n_in=19, n_hidden=16, n_out=4, seed=42):
        if weights_file is not None:
            data = np.load(weights_file)
            self.W1 = data['W1']
            self.b1 = data['b1']
            self.W2 = data['W2']
            self.b2 = data['b2']
        else:
            # Inicjalizacja He (pasuje do ReLU)
            rng = np.random.default_rng(seed)
            self.W1 = rng.standard_normal((n_in, n_hidden)).astype(np.float32) * np.sqrt(2.0 / n_in)
            self.b1 = np.zeros(n_hidden, dtype=np.float32)
            self.W2 = rng.standard_normal((n_hidden, n_out)).astype(np.float32) * np.sqrt(2.0 / n_hidden)
            self.b2 = np.zeros(n_out, dtype=np.float32)

    def forward(self, x):
        """Forward pass. x może być (19,) lub (B, 19)."""
        # warstwa ukryta + ReLU
        self._z1 = x @ self.W1 + self.b1
        self._h = np.maximum(0, self._z1)
        # warstwa wyjściowa (logity dla 4 klas)
        self._logits = self._h @ self.W2 + self.b2
        self._x = x
        return self._logits

    def classify(self, features):
        """Zwraca etykietę klasy (0=N, 1=L, 2=P, 3=X)."""
        logits = self.forward(features)
        if logits.ndim == 1:
            return int(np.argmax(logits))
        return np.argmax(logits, axis=-1)

    def backward(self, y_true, lr=0.01):
        """
        Backprop dla cross-entropy + softmax.
        y_true: (B,) indeksy klas.
        Używa stanu z ostatniego forward().
        """
        B = self._x.shape[0]

        # softmax (stabilny numerycznie)
        logits = self._logits - self._logits.max(axis=1, keepdims=True)
        exp_l = np.exp(logits)
        probs = exp_l / exp_l.sum(axis=1, keepdims=True)

        # gradient na logitach: (probs - one_hot) / B
        dlogits = probs.copy()
        dlogits[np.arange(B), y_true] -= 1.0
        dlogits /= B

        # gradienty W2, b2
        dW2 = self._h.T @ dlogits
        db2 = dlogits.sum(axis=0)

        # propagacja przez warstwę ukrytą
        dh = dlogits @ self.W2.T
        dz1 = dh * (self._z1 > 0).astype(np.float32)  # gradient ReLU

        dW1 = self._x.T @ dz1
        db1 = dz1.sum(axis=0)

        # SGD update
        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2

        # loss do zwrotu (średnia cross-entropy)
        loss = -np.log(probs[np.arange(B), y_true] + 1e-12).mean()
        return float(loss)

    def save(self, path):
        np.savez(path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2)


def train_mlp(model, X_train, y_train, X_val=None, y_val=None,
              epochs=50, batch_size=32, lr=0.01, lr_decay=0.98, verbose=True):
    """Trening minibatch SGD z prostym LR decay."""
    n = len(X_train)
    history = {'loss': [], 'val_acc': []}
    current_lr = lr

    for epoch in range(epochs):
        # shuffle
        perm = np.random.permutation(n)
        Xs, ys = X_train[perm], y_train[perm]

        losses = []
        for i in range(0, n, batch_size):
            xb = Xs[i:i + batch_size]
            yb = ys[i:i + batch_size]
            model.forward(xb)
            loss = model.backward(yb, lr=current_lr)
            losses.append(loss)

        avg_loss = float(np.mean(losses))
        history['loss'].append(avg_loss)
        current_lr *= lr_decay

        if X_val is not None:
            pred = model.classify(X_val)
            val_acc = float((pred == y_val).mean())
            history['val_acc'].append(val_acc)
            if verbose and (epoch + 1) % 5 == 0:
                print(f"Epoka {epoch+1:3d}/{epochs} | loss={avg_loss:.4f} | val_acc={val_acc*100:.2f}% | lr={current_lr:.4f}")
        elif verbose and (epoch + 1) % 5 == 0:
            print(f"Epoka {epoch+1:3d}/{epochs} | loss={avg_loss:.4f}")

    return history


def quantize_weights(model, bits=8):
    """
    Kwantyzacja wag do liczb stałoprzecinkowych (zgodnie z raportem).
    Zwraca kopię modelu z wagami jako int8, plus skalę.
    Tu pokazowo - zwracamy tylko wartości całkowite do inspekcji.
    """
    max_val = 2 ** (bits - 1) - 1  # np. 127 dla int8

    def q(arr):
        scale = np.abs(arr).max() / max_val if np.abs(arr).max() > 0 else 1.0
        return np.round(arr / scale).astype(np.int32), scale

    W1_q, s1 = q(model.W1)
    W2_q, s2 = q(model.W2)
    return {'W1_q': W1_q, 'W2_q': W2_q, 'scale_W1': s1, 'scale_W2': s2}


if __name__ == "__main__":
    mlp = SignMLP()
    print(f"W1: {mlp.W1.shape}, W2: {mlp.W2.shape}")
    # test forward
    x = np.random.randn(5, 19).astype(np.float32)
    out = mlp.forward(x)
    print(f"Wyjście: {out.shape}")
    print(f"Klasy: {mlp.classify(x)}")
