"""
Generator wektorow testowych dla etapu Deliver (testy FT-01..FT-07).
"""
import sys
import os
import argparse
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data_generator import generate_sample, LABEL_TO_IDX
from layer1_features import extract_features
from layer2_mlp import SignMLP
from layer3_voting import majority_vote

MIN_VOTES = 4
WINDOW = 6


def img_to_bin64(img):
    bits = img.flatten().astype(int)
    return ''.join(str(b) for b in bits)


def classify_window(model, frames):
    preds = []
    for frame in frames:
        feats = extract_features(frame)
        pred = model.classify(feats)
        preds.append(pred)
    voted = majority_vote(preds)
    counts = [0, 0, 0, 0]
    for p in preds:
        counts[p] += 1
    if counts[voted] >= MIN_VOTES:
        return voted
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

            decision = classify_window(model, frames)
            f_dec.write(f'{decision:X}\n')

    print(f"  FT-{test_id:02d}: {n_symbols} symbols")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', default=os.path.join(REPO_ROOT, 'sim', 'vectors'))
    args = parser.parse_args()

    weights_path = os.path.join(REPO_ROOT, 'weights.npz')
    if not os.path.exists(weights_path):
        print(f"ERROR: {weights_path} not found. Run main.py first.")
        sys.exit(1)

    model = SignMLP(weights_file=weights_path)
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
