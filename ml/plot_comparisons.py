"""Create comparison graphs from saved results; run after train_compare.py."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
BLUE, GREEN, INK = '#3676bb', '#128675', '#203249'

def main():
    report = json.loads((OUT / 'results.json').read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.spines.left': False, 'text.color': INK,
                         'axes.labelcolor': INK, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(3, 1, figsize=(11, 13), height_ratios=[3, 4.8, 3])
    fig.subplots_adjust(left=.30, right=.94, top=.90, bottom=.10, hspace=.65)
    fig.text(.06, .965, 'Machine Learning 2 | Algorithm comparisons', fontsize=20, weight='bold')
    fig.text(.06, .935, 'Measured results from the three supplied datasets · seed 42', fontsize=11)

    def base(ax, labels, title, xlabel, xmax):
        ax.set_yticks(np.arange(len(labels)), labels)
        ax.invert_yaxis()
        ax.set_title(title, loc='left', fontsize=13, weight='bold', pad=13)
        ax.set_xlabel(xlabel, labelpad=10)
        ax.set_xlim(0, xmax)
        ax.grid(axis='x', alpha=.16)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', length=0)

    rows = report['regression']; ax = axes[0]; y = np.arange(len(rows))
    labels = ['AdaBoost', 'Gradient Boosting', 'Histogram Gradient\nBoosting *']
    base(ax, labels, '01  Boosting · insurance charges', 'RMSE (dataset units) — lower is better', 6100)
    for offset, key, color, label in [(-.19, 'cv_rmse', BLUE, 'Training CV'), (.19, 'test_rmse', GREEN, 'Held-out test')]:
        bars = ax.barh(y+offset, [r[key] for r in rows], height=.32, color=color, label=label)
        ax.bar_label(bars, fmt='%.2f', padding=5, fontsize=9)
    ax.legend(loc='lower left', bbox_to_anchor=(0, -.45), ncol=2, frameon=False, fontsize=9)

    rows = report['classification']; ax = axes[1]; y = np.arange(len(rows))
    base(ax, ['Logistic Regression', 'RBF SVM', 'K Nearest Neighbors *', 'Random Forest', 'Decision Tree', 'Gaussian Naive Bayes'],
         '02  Classification · advertisement purchases', 'Accuracy (%) — higher is better', 110)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    for offset, key, color, label in [(-.19, 'cv_accuracy', BLUE, 'Training group CV'), (.19, 'test_accuracy', GREEN, 'Held-out test')]:
        bars = ax.barh(y+offset, [100*r[key] for r in rows], height=.32, color=color, label=label)
        ax.bar_label(bars, fmt='%.2f%%', padding=5, fontsize=9)
    ax.legend(loc='lower left', bbox_to_anchor=(0, -.29), ncol=2, frameon=False, fontsize=9)

    rows = report['clustering']; ax = axes[2]
    base(ax, ['K-Means *', 'Agglomerative Ward', 'Gaussian Mixture'],
         '03  Clustering · mall customer segments', 'Silhouette score — higher is better', 1.0)
    bars = ax.barh(np.arange(len(rows)), [r['silhouette'] for r in rows], height=.48, color=[GREEN, BLUE, BLUE])
    ax.bar_label(bars, labels=[f"{r['silhouette']:.4f}  (k={r['clusters']})" for r in rows], padding=7, fontsize=10)
    fig.text(.06, .025, '* Selected using training CV (supervised tasks) or silhouette (clustering).\nRandom Forest has the highest test accuracy; KNN is selected by CV. Metrics across tasks are not comparable.', fontsize=9)
    for extension in ['png', 'svg']:
        fig.savefig(OUT / f'algorithm_comparisons.{extension}', dpi=180, facecolor='white')
    plt.close(fig)

if __name__ == '__main__':
    main()
