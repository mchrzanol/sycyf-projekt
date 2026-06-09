"""
Generator wektorow testowych dla etapu Develop.
"""
import sys
import os
import argparse
import itertools
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data_generator import generate_sample, LABEL_TO_IDX, IDX_TO_LABEL
from layer1_features import extract_features
from layer2_mlp import SignMLP
from layer3_voting import majority_vote


def img_to_bin64(img):
    bits = img.flatten().astype(int)
    return ''.join(str(b) for b in bits)


def gen_layer1(out_dir, n=100, seed=42):
    np.random.seed(seed)
    labels = list(LABEL_TO_IDX.keys())

    with open(os.path.join(out_dir, 'layer1_images.txt'), 'w') as f_img, \
         open(os.path.join(out_dir, 'layer1_features.txt'), 'w') as f_feat:
        for i in range(n):
            label = labels[i % len(labels)]
            img = generate_sample(label, noise=0.05, max_shift=2)
            f_img.write(img_to_bin64(img) + '\n')
            feats = extract_features(img)
            hex_vals = ' '.join(f'{int(v):02X}' for v in feats)
            f_feat.write(hex_vals + '\n')

    print(f"  Layer 1: {n} vectors -> layer1_images.txt, layer1_features.txt")


def gen_layer2(out_dir, n_train=40, n_test=200, seed=42):
    np.random.seed(seed)
    labels = list(LABEL_TO_IDX.keys())
    model = SignMLP(weights_file=os.path.join(REPO_ROOT, 'weights.npz'))

    for prefix, count in [('train', n_train), ('test', n_test)]:
        with open(os.path.join(out_dir, f'layer2_{prefix}_features.txt'), 'w') as f_feat, \
             open(os.path.join(out_dir, f'layer2_{prefix}_labels.txt'), 'w') as f_lbl:
            noise = 0.0 if prefix == 'train' else 0.05
            for i in range(count):
                label = labels[i % len(labels)]
                img = generate_sample(label, noise=noise, max_shift=2)
                feats = extract_features(img)
                pred = model.classify(feats)
                hex_vals = ' '.join(f'{int(v):02X}' for v in feats)
                f_feat.write(hex_vals + '\n')
                f_lbl.write(f'{pred}\n')

    print(f"  Layer 2: {n_train} train + {n_test} test vectors")


def gen_layer3(out_dir):
    with open(os.path.join(out_dir, 'layer3_votes.txt'), 'w') as f_in, \
         open(os.path.join(out_dir, 'layer3_decisions.txt'), 'w') as f_out:
        for combo in itertools.product(range(4), repeat=6):
            f_in.write(''.join(str(c) for c in combo) + '\n')
            result = majority_vote(list(combo))
            f_out.write(f'{result}\n')

    print(f"  Layer 3: 4096 exhaustive combinations")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=os.path.join(REPO_ROOT, 'sim', 'vectors'))
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"Generating vectors (seed={args.seed}) -> {args.out}")

    gen_layer1(args.out, n=100, seed=args.seed)
    gen_layer2(args.out, seed=args.seed)
    gen_layer3(args.out)
    print("Done.")


if __name__ == "__main__":
    main()
