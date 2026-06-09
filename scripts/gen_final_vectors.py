"""
Generator wektorow testowych dla etapu Deliver (testy FT-01..FT-07).
Uses exact HDL-matching golden model (feature extraction + Q4.4 MLP).
"""
import sys
import os
import argparse
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data_generator import generate_sample, LABEL_TO_IDX

MIN_VOTES = 4
WINDOW = 6


def img_to_bin64(img):
    bits = img.flatten().astype(int)
    return ''.join(str(b) for b in reversed(bits))


def to_signed8(v):
    return v - 256 if v >= 128 else v


class HdlGoldenModel:
    """Exact Python simulation of the complete HDL pipeline."""

    def __init__(self, hex_path, inv_lut_path):
        with open(hex_path) as f:
            self.rom = [int(line.strip(), 16) for line in f]
        with open(inv_lut_path) as f:
            self.inv_lut = [0] + [int(line.strip(), 16) for line in f]

    def extract_features_hdl(self, img):
        row_sum = [0] * 8
        col_sum = [0] * 8
        for r in range(8):
            for c in range(8):
                row_sum[r] += int(img[r, c])
                col_sum[c] += int(img[r, c])

        total = sum(row_sum)

        sum_x = 0
        for c in range(8):
            sum_x += col_sum[c] * c
        sum_y = 0
        for r in range(8):
            sum_y += row_sum[r] * r

        if total == 0:
            cm_x = 14
            cm_y = 14
        else:
            inv = self.inv_lut[total]
            cmx_full = int(sum_x) * int(inv)
            cmy_full = int(sum_y) * int(inv)
            cm_x = (cmx_full >> 8) & 0x1F
            cm_y = (cmy_full >> 8) & 0x1F

        feat = []
        for r in range(8):
            feat.append(row_sum[r] & 0x0F)
        for c in range(8):
            feat.append(col_sum[c] & 0x0F)
        feat.append(cm_x & 0x1F)
        feat.append(cm_y & 0x1F)
        feat.append((total >> 2) & 0x1F)
        return feat

    def classify_single(self, img):
        feat = self.extract_features_hdl(img)

        hidden = [0] * 16
        for j in range(16):
            acc = 0
            for i in range(19):
                w = to_signed8(self.rom[j * 19 + i])
                acc += feat[i] * w
            bias = to_signed8(self.rom[304 + j])
            acc += bias
            if acc >= 0:
                hidden[j] = (acc >> 4) & 0xFF
            else:
                hidden[j] = 0

        logits = [0] * 4
        for j in range(4):
            acc = 0
            for i in range(16):
                w = to_signed8(self.rom[320 + j * 16 + i])
                acc += hidden[i] * w
            bias = to_signed8(self.rom[384 + j])
            acc += bias
            logits[j] = acc

        best = 0
        for c in range(1, 4):
            if logits[c] > logits[best]:
                best = c
        return best

    def classify_window(self, frames):
        preds = [self.classify_single(f) for f in frames]
        counts = [0, 0, 0, 0]
        for p in preds:
            counts[p] += 1
        winner = 0
        for c in range(1, 4):
            if counts[c] > counts[winner]:
                winner = c
        if counts[winner] >= MIN_VOTES:
            return winner
        else:
            return 0xF


def gen_test(out_dir, test_id, model, rng, n_symbols, noise, max_shift, random_frames=False):
    labels = list(LABEL_TO_IDX.keys())
    frame_file = os.path.join(out_dir, f'ft{test_id:02d}_frames.txt')
    dec_file = os.path.join(out_dir, f'ft{test_id:02d}_decisions.txt')

    with open(frame_file, 'w') as f_fr, open(dec_file, 'w') as f_dec:
        for sym in range(n_symbols):
            frames = []
            if random_frames:
                for _ in range(WINDOW):
                    img = (rng.random((8, 8)) > 0.5).astype(np.uint8)
                    frames.append(img)
            else:
                label = labels[sym % len(labels)]
                for _ in range(WINDOW):
                    old_state = np.random.get_state()
                    np.random.seed(rng.integers(0, 2**31))
                    img = generate_sample(label, noise=noise, max_shift=max_shift)
                    np.random.set_state(old_state)
                    frames.append(img)

            for img in frames:
                f_fr.write(img_to_bin64(img) + '\n')

            decision = model.classify_window(frames)
            f_dec.write(f'{decision:X}\n')

    print(f"  FT-{test_id:02d}: {n_symbols} symbols")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', default=os.path.join(REPO_ROOT, 'sim', 'vectors'))
    args = parser.parse_args()

    hex_path = os.path.join(REPO_ROOT, 'weights_q44.hex')
    inv_lut_path = os.path.join(REPO_ROOT, 'inv_lut.hex')
    for p in [hex_path, inv_lut_path]:
        if not os.path.exists(p):
            print(f"ERROR: {p} not found.")
            sys.exit(1)

    model = HdlGoldenModel(hex_path, inv_lut_path)
    os.makedirs(args.out, exist_ok=True)
    print(f"Generating final test vectors (seed={args.seed}) -> {args.out}")

    gen_test(args.out, 1, model, np.random.default_rng(args.seed + 1),
             n_symbols=200, noise=0.0, max_shift=0)
    gen_test(args.out, 2, model, np.random.default_rng(args.seed + 2),
             n_symbols=1000, noise=0.05, max_shift=2)
    gen_test(args.out, 3, model, np.random.default_rng(args.seed + 3),
             n_symbols=100, noise=0.0, max_shift=0, random_frames=True)
    gen_test(args.out, 4, model, np.random.default_rng(args.seed + 4),
             n_symbols=1000, noise=0.0, max_shift=3)
    gen_test(args.out, 5, model, np.random.default_rng(args.seed + 5),
             n_symbols=1000, noise=0.15, max_shift=0)
    gen_test(args.out, 6, model, np.random.default_rng(args.seed + 6),
             n_symbols=1000, noise=0.05, max_shift=2)
    gen_test(args.out, 7, model, np.random.default_rng(args.seed + 7),
             n_symbols=20, noise=0.05, max_shift=2)

    print("Done.")


if __name__ == "__main__":
    main()
