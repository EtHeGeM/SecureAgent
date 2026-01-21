#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


FIG_W, FIG_H = 12.8, 7.2
DPI = 150
SEED = 7

COLORS = {
    "black": "#111111",
    "gray": "#444444",
    "light_gray": "#c7c7c7",
    "blue": "#1f77b4",
    "orange": "#ff7f0e",
    "green": "#2ca02c",
    "red": "#d62728",
    "purple": "#9467bd",
    "teal": "#17becf",
}


def apply_style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 14,
            "mathtext.fontset": "dejavusans",
            "axes.linewidth": 1.5,
            "lines.linewidth": 2.0,
            "patch.linewidth": 1.5,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def new_fig(nrows=1, ncols=1, gridspec_kw=None):
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(FIG_W, FIG_H), dpi=DPI, gridspec_kw=gridspec_kw
    )
    fig.add_artist(
        patches.Rectangle(
            (0, 0),
            1,
            1,
            transform=fig.transFigure,
            fc="white",
            ec="none",
            alpha=0.0,
            zorder=-1000,
        )
    )
    return fig, axes


def save_fig(fig, outpath):
    fig.savefig(outpath, bbox_inches="tight", pad_inches=0.1, dpi=DPI)
    plt.close(fig)


def add_full_background(ax, color="white"):
    ax.add_patch(
        patches.Rectangle(
            (0, 0),
            1,
            1,
            transform=ax.transAxes,
            fc=color,
            ec=color,
            zorder=-100,
        )
    )


def add_round_box(ax, center, size, text, fc="white", ec=None, lw=1.8, text_size=12):
    if ec is None:
        ec = COLORS["black"]
    x, y = center
    w, h = size
    rect = patches.FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(rect)
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=text_size,
        color=COLORS["black"],
    )


def add_arrow(ax, start, end, color=None, lw=1.6):
    if color is None:
        color = COLORS["black"]
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, shrinkA=0, shrinkB=0),
    )


def draw_grid(ax, origin, rows, cols, cell_size, color=None, lw=1.0):
    if color is None:
        color = COLORS["gray"]
    x0, y0 = origin
    for r in range(rows + 1):
        y = y0 + r * cell_size
        ax.plot([x0, x0 + cols * cell_size], [y, y], color=color, lw=lw)
    for c in range(cols + 1):
        x = x0 + c * cell_size
        ax.plot([x, x], [y0, y0 + rows * cell_size], color=color, lw=lw)


def gaussian_kernel(size=9, sigma=2.0):
    ax = np.arange(size) - size // 2
    kernel_1d = np.exp(-(ax**2) / (2 * sigma**2))
    kernel_1d /= kernel_1d.sum()
    kernel_2d = np.outer(kernel_1d, kernel_1d)
    kernel_2d /= kernel_2d.sum()
    return kernel_1d, kernel_2d


def convolve2d(img, kernel):
    k = kernel.shape[0]
    pad = k // 2
    padded = np.pad(img, pad, mode="edge")
    out = np.zeros_like(img, dtype=float)
    for i in range(k):
        for j in range(k):
            out += kernel[i, j] * padded[i : i + img.shape[0], j : j + img.shape[1]]
    return out


def hsv_to_rgb(h, s, v):
    h = np.mod(h, 1.0)
    i = np.floor(h * 6.0).astype(int)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i = i % 6
    r = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
        [v, q, p, p, t, v],
        default=0,
    )
    g = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
        [t, v, v, q, p, p],
        default=0,
    )
    b = np.select(
        [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
        [p, p, t, v, v, q],
        default=0,
    )
    return np.stack([r, g, b], axis=-1)


def resize_nearest(img, new_size):
    h, w = img.shape[:2]
    new_h, new_w = new_size
    ys = (np.linspace(0, h - 1, new_h)).astype(int)
    xs = (np.linspace(0, w - 1, new_w)).astype(int)
    if img.ndim == 2:
        return img[ys][:, xs]
    return img[ys][:, xs, :]


def gaussian_blur(img, sigma=1.5):
    size = int(6 * sigma + 1)
    if size % 2 == 0:
        size += 1
    _, kernel = gaussian_kernel(size=size, sigma=sigma)
    return convolve2d(img, kernel)


def sobel_edges(img):
    gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
    gy = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=float)
    ix = convolve2d(img, gx)
    iy = convolve2d(img, gy)
    mag = np.sqrt(ix**2 + iy**2)
    mag /= mag.max() + 1e-9
    return mag


def make_synthetic_image(size=256):
    img = np.zeros((size, size), dtype=float) + 0.15
    r0, r1 = int(0.15 * size), int(0.45 * size)
    c0, c1 = int(0.12 * size), int(0.43 * size)
    img[r0:r1, c0:c1] = 0.8
    yy, xx = np.ogrid[:size, :size]
    cx, cy = int(0.7 * size), int(0.3 * size)
    radius = int(0.12 * size)
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2
    img[mask] = 0.9
    r2, r3 = int(0.62 * size), int(0.86 * size)
    c2, c3 = int(0.55 * size), int(0.86 * size)
    img[r2:r3, c2:c3] = 0.6
    diag_start = int(0.12 * size)
    diag_end = int(0.78 * size)
    for i in range(diag_start, diag_end):
        img[i, i] = 1.0
    gradient = np.linspace(0, 0.2, size)[None, :]
    img = np.clip(img + gradient, 0, 1)
    return img


def make_color_scene(size=256):
    base = np.ones((size, size, 3), dtype=float) * 0.12
    base[:, :, 0] += np.linspace(0, 0.2, size)[None, :]
    base[40:130, 30:140, :] = np.array([0.2, 0.6, 0.85])
    yy, xx = np.ogrid[:size, :size]
    mask = (xx - 185) ** 2 + (yy - 90) ** 2 <= 28**2
    base[mask] = np.array([0.2, 0.8, 0.45])
    base[150:220, 150:230, :] = np.array([0.75, 0.3, 0.3])
    base = np.clip(base, 0, 1)
    bboxes = [
        (30, 40, 110, 90, "object A"),
        (157, 62, 56, 56, "object B"),
        (150, 150, 80, 70, "object C"),
    ]
    return base, bboxes


def fig_cover_bg(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax, color="white")
    h, w = 360, 640
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    r_norm = r / r.max()
    vignette = r_norm**1.7
    overlay = np.zeros((h, w, 4), dtype=float)
    overlay[..., 3] = 0.35 * vignette
    ax.imshow(overlay, extent=[0, 1, 0, 1], origin="lower")
    for x in np.linspace(0, 1, 13):
        ax.plot([x, x], [0, 1], color=COLORS["light_gray"], lw=1, alpha=0.35)
    for y in np.linspace(0, 1, 8):
        ax.plot([0, 1], [y, y], color=COLORS["light_gray"], lw=1, alpha=0.35)
    rng = np.random.default_rng(SEED)
    pts = rng.uniform(0.08, 0.92, size=(32, 2))
    for i in range(len(pts)):
        idx = rng.choice(len(pts), size=2, replace=False)
        for j in idx:
            ax.plot(
                [pts[i, 0], pts[j, 0]],
                [pts[i, 1], pts[j, 1]],
                color=COLORS["blue"],
                alpha=0.25,
                lw=1.2,
            )
    ax.scatter(pts[:, 0], pts[:, 1], s=18, color=COLORS["blue"], alpha=0.7)
    save_fig(fig, outpath)


def fig_cv_taxonomy(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    add_round_box(ax, (0.5, 0.78), (0.28, 0.12), "Computer Vision")
    labels = ["Classification", "Detection", "Segmentation", "OCR", "Tracking"]
    xs = np.linspace(0.1, 0.9, len(labels))
    for x, label in zip(xs, labels):
        add_round_box(ax, (x, 0.32), (0.18, 0.1), label, fc="#f7f7f7")
        add_arrow(ax, (0.5, 0.72), (x, 0.38), lw=1.4)
    save_fig(fig, outpath)


def fig_pipeline_overview(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    stages = ["Data", "Preprocess", "Model", "Train", "Evaluate", "Deploy"]
    xs = np.linspace(0.08, 0.92, len(stages))
    for x, label in zip(xs, stages):
        add_round_box(ax, (x, 0.5), (0.13, 0.1), label)
    for i in range(len(xs) - 1):
        add_arrow(ax, (xs[i] + 0.07, 0.5), (xs[i + 1] - 0.07, 0.5))
    save_fig(fig, outpath)


def fig_dataset_split(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.1, 0.75, "split then fit", fontsize=14, color=COLORS["gray"])
    x0, y0, w, h = 0.1, 0.45, 0.8, 0.12
    ax.add_patch(patches.Rectangle((x0, y0), w * 0.7, h, fc=COLORS["blue"], ec="none", alpha=0.8))
    ax.add_patch(
        patches.Rectangle((x0 + w * 0.7, y0), w * 0.15, h, fc=COLORS["orange"], ec="none", alpha=0.8)
    )
    ax.add_patch(
        patches.Rectangle((x0 + w * 0.85, y0), w * 0.15, h, fc=COLORS["green"], ec="none", alpha=0.8)
    )
    ax.text(x0 + w * 0.35, y0 + h / 2, "Train", color="white", ha="center", va="center", fontsize=13)
    ax.text(x0 + w * 0.775, y0 + h / 2, "Val", color="white", ha="center", va="center", fontsize=13)
    ax.text(x0 + w * 0.925, y0 + h / 2, "Test", color="white", ha="center", va="center", fontsize=13)
    save_fig(fig, outpath)


def fig_normalization(outpath):
    rng = np.random.default_rng(SEED)
    data = rng.normal(loc=5.0, scale=2.0, size=800)
    mu, sigma = data.mean(), data.std()
    norm = (data - mu) / sigma
    fig, axes = new_fig(1, 3)
    left, ax1, ax2 = axes
    left.set_axis_off()
    add_full_background(left)
    left.set_xlim(0, 1)
    left.set_ylim(0, 1)
    left.text(0.1, 0.55, r"$x=[x_1,x_2,x_3]$", fontsize=14)
    add_arrow(left, (0.38, 0.55), (0.62, 0.55))
    left.text(0.66, 0.55, r"$\frac{x-\mu}{\sigma}$", fontsize=14)
    left.text(0.1, 0.35, r"$\mu=%.2f,\ \sigma=%.2f$" % (mu, sigma), fontsize=12, color=COLORS["gray"])
    ax1.hist(data, bins=20, color=COLORS["blue"], alpha=0.85)
    ax1.set_title("Before")
    ax1.set_xlabel("x")
    ax1.set_ylabel("count")
    ax2.hist(norm, bins=20, color=COLORS["green"], alpha=0.85)
    ax2.set_title("After")
    ax2.set_xlabel("z")
    ax2.set_ylabel("count")
    save_fig(fig, outpath)


def fig_histogram(outpath):
    rng = np.random.default_rng(SEED)
    vals = np.concatenate(
        [
            rng.normal(80, 18, 600),
            rng.normal(170, 22, 400),
        ]
    )
    vals = np.clip(vals, 0, 255)
    fig, ax = new_fig()
    bins = np.linspace(0, 255, 32)
    counts, edges, _ = ax.hist(vals, bins=bins, color=COLORS["blue"], alpha=0.75)
    ax.set_xlabel("intensity")
    ax.set_ylabel("count")
    cdf = np.cumsum(counts) / counts.sum()
    ax2 = ax.twinx()
    ax2.plot(edges[:-1], cdf, color=COLORS["orange"])
    ax2.set_ylabel("CDF")
    ax.set_title("Histogram + CDF")
    save_fig(fig, outpath)


def fig_gaussian_kernel(outpath):
    k1d, k2d = gaussian_kernel(size=9, sigma=1.8)
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    im = ax0.imshow(k2d, cmap="viridis")
    ax0.set_title("2D Gaussian kernel")
    ax0.set_xticks([])
    ax0.set_yticks([])
    fig.colorbar(im, ax=ax0, fraction=0.046, pad=0.04)
    x = np.arange(len(k1d)) - len(k1d) // 2
    ax1.plot(x, k1d, marker="o", color=COLORS["purple"])
    ax1.set_title("1D Gaussian")
    ax1.set_xlabel("x")
    ax1.set_ylabel("weight")
    ax1.grid(True, alpha=0.2)
    save_fig(fig, outpath)


def fig_conv_stride_padding(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    origin = (0.12, 0.18)
    cell = 0.08
    rows = cols = 7
    for r in range(rows):
        for c in range(cols):
            x = origin[0] + c * cell
            y = origin[1] + r * cell
            if r in (0, rows - 1) or c in (0, cols - 1):
                ax.add_patch(
                    patches.Rectangle((x, y), cell, cell, fc="#efefef", ec="none")
                )
    draw_grid(ax, origin, rows, cols, cell_size=cell, color=COLORS["gray"], lw=1.0)
    ax.text(0.12, 0.8, "padding", color=COLORS["gray"], fontsize=12)
    kx, ky = origin[0] + cell * 2, origin[1] + cell * 2
    ax.add_patch(
        patches.Rectangle((kx, ky), cell * 3, cell * 3, ec=COLORS["blue"], fc="none", lw=2.0)
    )
    kx2 = kx + cell * 2
    ax.add_patch(
        patches.Rectangle(
            (kx2, ky),
            cell * 3,
            cell * 3,
            ec=COLORS["blue"],
            fc="none",
            lw=1.6,
            ls="--",
        )
    )
    add_arrow(ax, (kx + cell * 3.1, ky + cell * 1.5), (kx2 - 0.01, ky + cell * 1.5))
    ax.text(kx + cell * 1.2, ky + cell * 3.2, "kernel", fontsize=12, color=COLORS["blue"])
    ax.text(kx + cell * 3.1, ky + cell * 1.9, "stride=2", fontsize=12, color=COLORS["gray"])
    save_fig(fig, outpath)


def fig_relu_plot(outpath):
    x = np.linspace(-3, 3, 200)
    relu = np.maximum(0, x)
    der = np.where(x >= 0, 1, 0)
    fig, axes = new_fig(2, 1, gridspec_kw={"height_ratios": [1, 1]})
    ax0, ax1 = axes
    ax0.plot(x, relu, color=COLORS["blue"])
    ax0.axhline(0, color=COLORS["gray"], lw=1)
    ax0.axvline(0, color=COLORS["gray"], lw=1)
    ax0.set_title("ReLU")
    ax0.set_xlabel("x")
    ax0.set_ylabel("f(x)")
    ax1.plot(x, der, color=COLORS["orange"])
    ax1.axhline(0, color=COLORS["gray"], lw=1)
    ax1.axvline(0, color=COLORS["gray"], lw=1)
    ax1.set_ylim(-0.2, 1.2)
    ax1.set_title("Derivative")
    ax1.set_xlabel("x")
    ax1.set_ylabel("f'(x)")
    save_fig(fig, outpath)


def fig_softmax_plot(outpath):
    logits = np.array([1.2, 0.3, -0.7])
    exps = np.exp(logits - logits.max())
    probs = exps / exps.sum()
    labels = ["c1", "c2", "c3"]
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    ax0.bar(labels, logits, color=COLORS["blue"], alpha=0.85)
    ax0.set_title("Logits")
    ax0.set_ylabel("score")
    ax1.bar(labels, probs, color=COLORS["green"], alpha=0.85)
    ax1.set_title("Softmax")
    ax1.set_ylabel("prob")
    ax1.set_ylim(0, 1)
    save_fig(fig, outpath)


def fig_loss_landscape(outpath):
    x = np.linspace(-1, 5, 400)
    y = (x - 2) ** 2 + 0.5
    fig, ax = new_fig()
    ax.plot(x, y, color=COLORS["blue"])
    ax.set_xlabel("parameter")
    ax.set_ylabel("loss")
    ax.set_title("Loss landscape")
    steps = [4.5]
    lr = 0.4
    for _ in range(4):
        grad = 2 * (steps[-1] - 2)
        steps.append(steps[-1] - lr * grad)
    for i in range(len(steps) - 1):
        x0, x1 = steps[i], steps[i + 1]
        y0, y1 = (x0 - 2) ** 2 + 0.5, (x1 - 2) ** 2 + 0.5
        ax.scatter([x0], [y0], color=COLORS["orange"], zorder=5)
        add_arrow(ax, (x0, y0), (x1, y1), color=COLORS["orange"], lw=1.4)
    ax.scatter([steps[-1]], [(steps[-1] - 2) ** 2 + 0.5], color=COLORS["orange"], zorder=5)
    save_fig(fig, outpath)


def fig_confusion_matrix(outpath):
    mat = np.array([[45, 5], [3, 47]])
    fig, ax = new_fig()
    im = ax.imshow(mat, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Pred +", "Pred -"])
    ax.set_yticklabels(["Actual +", "Actual -"])
    labels = [["TP", "FN"], ["FP", "TN"]]
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{labels[i][j]}\n{mat[i, j]}",
                ha="center",
                va="center",
                color=COLORS["black"],
                fontsize=13,
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Confusion matrix")
    save_fig(fig, outpath)


def fig_iou_diagram(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    rect_a = patches.Rectangle((0.18, 0.3), 0.45, 0.35, fc=COLORS["blue"], alpha=0.35, ec=COLORS["blue"])
    rect_b = patches.Rectangle((0.38, 0.45), 0.45, 0.35, fc=COLORS["orange"], alpha=0.35, ec=COLORS["orange"])
    ax.add_patch(rect_a)
    ax.add_patch(rect_b)
    ix0 = max(0.18, 0.38)
    iy0 = max(0.3, 0.45)
    ix1 = min(0.18 + 0.45, 0.38 + 0.45)
    iy1 = min(0.3 + 0.35, 0.45 + 0.35)
    if ix1 > ix0 and iy1 > iy0:
        ax.add_patch(
            patches.Rectangle(
                (ix0, iy0), ix1 - ix0, iy1 - iy0, fc=COLORS["purple"], alpha=0.6, ec="none"
            )
        )
    ax.text(0.25, 0.58, "A", fontsize=14, color=COLORS["blue"])
    ax.text(0.72, 0.74, "B", fontsize=14, color=COLORS["orange"])
    ax.text(0.38, 0.25, r"$IoU=\frac{|A\cap B|}{|A\cup B|}$", fontsize=16)
    save_fig(fig, outpath)


def fig_pr_curve(outpath):
    recall = np.linspace(0, 1, 30)
    precision = 1 - 0.7 * recall + 0.05 * np.cos(5 * recall)
    precision = np.clip(precision, 0.2, 1.0)
    precision = np.maximum.accumulate(precision[::-1])[::-1]
    fig, ax = new_fig()
    ax.plot(recall, precision, color=COLORS["blue"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall curve")
    idx = [5, 12, 20, 27]
    thresholds = [0.8, 0.6, 0.4, 0.2]
    for i, t in zip(idx, thresholds):
        ax.scatter([recall[i]], [precision[i]], color=COLORS["orange"], zorder=5)
        ax.text(recall[i] + 0.02, precision[i] - 0.05, f"t={t}", fontsize=11)
    save_fig(fig, outpath)


def fig_map_interp(outpath):
    recall = np.array([0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0])
    precision = np.array([1.0, 0.9, 0.75, 0.78, 0.6, 0.55, 0.4])
    interp = np.array([precision[i:].max() for i in range(len(precision))])
    fig, ax = new_fig()
    ax.plot(recall, precision, marker="o", color=COLORS["gray"], label="raw")
    ax.step(recall, interp, where="post", color=COLORS["blue"], label="interp")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Interpolated PR")
    ax.legend(loc="lower left")
    ax.text(0.52, 0.15, r"$P_{interp}(R)=\max_{R'\geq R} P(R')$", fontsize=12)
    save_fig(fig, outpath)


def fig_canny_steps(outpath):
    img = make_synthetic_image(256)
    blurred = gaussian_blur(img, sigma=1.6)
    grad = sobel_edges(blurred)
    edges = (grad > 0.35).astype(float)
    fig, axes = new_fig(2, 2)
    titles = ["Original", "Blurred", "Gradient", "Edges"]
    images = [img, blurred, grad, edges]
    for ax, title, im in zip(axes.flatten(), titles, images):
        ax.imshow(im, cmap="gray", vmin=0, vmax=1)
        ax.set_title(title)
        ax.set_axis_off()
    save_fig(fig, outpath)


def fig_sobel_edges(outpath):
    img = make_synthetic_image(256)
    grad = sobel_edges(img)
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    ax0.imshow(img, cmap="gray", vmin=0, vmax=1)
    ax0.set_title("Original")
    ax0.set_axis_off()
    ax1.imshow(grad, cmap="gray", vmin=0, vmax=1)
    ax1.set_title("Sobel magnitude")
    ax1.set_axis_off()
    save_fig(fig, outpath)


def fig_contours_before_after(outpath):
    img = make_synthetic_image(256)
    grad = sobel_edges(img)
    edges = grad > 0.35
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    ax0.imshow(edges, cmap="gray")
    ax0.set_title("Edges")
    ax0.set_axis_off()
    ax1.imshow(img, cmap="gray", vmin=0, vmax=1)
    overlay = np.zeros((img.shape[0], img.shape[1], 4), dtype=float)
    overlay[edges] = np.array([1.0, 0.0, 0.0, 0.8])
    ax1.imshow(overlay)
    ax1.set_title("Contours overlay")
    ax1.set_axis_off()
    save_fig(fig, outpath)


def fig_bbox_overlay(outpath):
    img, bboxes = make_color_scene(256)
    fig, ax = new_fig()
    ax.imshow(img, vmin=0, vmax=1)
    ax.set_axis_off()
    for x, y, w, h, label in bboxes:
        ax.add_patch(
            patches.Rectangle((x, y), w, h, fill=False, ec=COLORS["red"], lw=2.0)
        )
        ax.text(
            x + 2,
            y - 5,
            label,
            fontsize=10,
            color="white",
            bbox=dict(boxstyle="round,pad=0.2", fc=COLORS["red"], ec="none"),
        )
    save_fig(fig, outpath)


def fig_yolo_decode(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    cell = patches.Rectangle((0.1, 0.2), 0.35, 0.35, ec=COLORS["gray"], fc="#f5f5f5")
    ax.add_patch(cell)
    anchor = patches.Rectangle((0.18, 0.25), 0.18, 0.2, ec=COLORS["blue"], fc="none", ls="--", lw=1.6)
    ax.add_patch(anchor)
    decoded = patches.Rectangle((0.23, 0.28), 0.24, 0.26, ec=COLORS["green"], fc="none", lw=2.0)
    ax.add_patch(decoded)
    add_arrow(ax, (0.27, 0.35), (0.23, 0.32), color=COLORS["orange"], lw=1.5)
    ax.text(0.12, 0.58, "grid cell", fontsize=12, color=COLORS["gray"])
    ax.text(0.18, 0.47, "anchor", fontsize=11, color=COLORS["blue"])
    ax.text(0.22, 0.56, "decoded box", fontsize=11, color=COLORS["green"])
    ax.text(
        0.55,
        0.5,
        r"$b_x=\sigma(t_x)+c_x$" "\n" r"$b_y=\sigma(t_y)+c_y$" "\n" r"$b_w=e^{t_w}a_w$" "\n" r"$b_h=e^{t_h}a_h$",
        fontsize=12,
        color=COLORS["black"],
    )
    save_fig(fig, outpath)


def fig_nms_example(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    boxes = [
        (0.2, 0.35, 0.35, 0.4, 0.92),
        (0.25, 0.4, 0.32, 0.36, 0.85),
        (0.18, 0.32, 0.38, 0.42, 0.8),
        (0.55, 0.2, 0.3, 0.3, 0.6),
    ]
    selected = boxes[0]
    for x, y, w, h, score in boxes:
        if (x, y, w, h, score) == selected:
            ax.add_patch(
                patches.Rectangle((x, y), w, h, fill=False, ec=COLORS["green"], lw=2.4)
            )
            ax.text(x, y + h + 0.02, f"{score:.2f}", color=COLORS["green"], fontsize=12)
        else:
            ax.add_patch(
                patches.Rectangle(
                    (x, y), w, h, fill=False, ec=COLORS["red"], lw=1.6, ls="--", alpha=0.7
                )
            )
            ax.text(x, y + h + 0.02, f"{score:.2f}", color=COLORS["red"], fontsize=11)
    ax.text(0.58, 0.58, "suppressed", color=COLORS["red"], fontsize=12)
    ax.text(0.22, 0.78, "selected", color=COLORS["green"], fontsize=12)
    save_fig(fig, outpath)


def fig_attention_matrix(outpath):
    rng = np.random.default_rng(SEED)
    n = 6
    logits = rng.normal(size=(n, n))
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    attn = exp / exp.sum(axis=1, keepdims=True)
    fig, ax = new_fig()
    im = ax.imshow(attn, cmap="magma", vmin=0, vmax=1)
    labels = [f"t{i+1}" for i in range(n)]
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_title("Attention weights")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_fig(fig, outpath)


def fig_mha(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    add_round_box(ax, (0.08, 0.5), (0.1, 0.1), "X")
    head_y = [0.75, 0.5, 0.25]
    for i, y in enumerate(head_y, start=1):
        add_round_box(ax, (0.28, y), (0.12, 0.08), "Q,K,V", fc="#f6f6f6", text_size=10)
        add_round_box(ax, (0.45, y), (0.14, 0.08), f"Head {i}", fc="#f6f6f6", text_size=10)
        add_arrow(ax, (0.13, 0.5), (0.22, y))
        add_arrow(ax, (0.34, y), (0.38, y))
    add_round_box(ax, (0.66, 0.5), (0.14, 0.1), "Concat")
    add_round_box(ax, (0.82, 0.5), (0.12, 0.1), "Linear")
    for y in head_y:
        add_arrow(ax, (0.52, y), (0.59, 0.5))
    add_arrow(ax, (0.73, 0.5), (0.76, 0.5))
    save_fig(fig, outpath)


def fig_transformer_block(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    x = 0.5
    add_round_box(ax, (x, 0.9), (0.12, 0.07), "Input", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (x, 0.78), (0.12, 0.07), "LN", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (x, 0.66), (0.16, 0.07), "MHA", fc="#f6f6f6", text_size=10)
    ax.add_patch(patches.Circle((x, 0.56), 0.03, ec=COLORS["black"], fc="white", lw=1.5))
    ax.text(x, 0.56, "+", ha="center", va="center", fontsize=12)
    add_round_box(ax, (x, 0.46), (0.12, 0.07), "LN", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (x, 0.34), (0.16, 0.07), "MLP", fc="#f6f6f6", text_size=10)
    ax.add_patch(patches.Circle((x, 0.24), 0.03, ec=COLORS["black"], fc="white", lw=1.5))
    ax.text(x, 0.24, "+", ha="center", va="center", fontsize=12)
    add_round_box(ax, (x, 0.12), (0.12, 0.07), "Output", fc="#f6f6f6", text_size=10)
    add_arrow(ax, (x, 0.86), (x, 0.81))
    add_arrow(ax, (x, 0.74), (x, 0.69))
    add_arrow(ax, (x, 0.63), (x, 0.59))
    add_arrow(ax, (x, 0.53), (x, 0.49))
    add_arrow(ax, (x, 0.41), (x, 0.37))
    add_arrow(ax, (x, 0.31), (x, 0.27))
    add_arrow(ax, (x, 0.21), (x, 0.16))
    ax.plot([0.28, 0.28, x - 0.03], [0.9, 0.56, 0.56], color=COLORS["gray"], lw=1.4)
    ax.plot([0.28, 0.28, x - 0.03], [0.56, 0.24, 0.24], color=COLORS["gray"], lw=1.4)
    save_fig(fig, outpath)


def fig_patchify(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    img = make_synthetic_image(80)
    ax.imshow(img, cmap="gray", extent=[0.05, 0.45, 0.2, 0.8], vmin=0, vmax=1)
    for i in range(1, 4):
        x = 0.05 + i * (0.4 / 4)
        ax.plot([x, x], [0.2, 0.8], color=COLORS["black"], lw=1)
        y = 0.2 + i * (0.6 / 4)
        ax.plot([0.05, 0.45], [y, y], color=COLORS["black"], lw=1)
    add_arrow(ax, (0.48, 0.5), (0.58, 0.5))
    for i in range(6):
        y = 0.75 - i * 0.1
        ax.add_patch(
            patches.Rectangle((0.6, y), 0.25, 0.07, fc="#f6f6f6", ec=COLORS["black"], lw=1.2)
        )
    ax.text(0.06, 0.82, "patches", fontsize=12, color=COLORS["gray"])
    ax.text(0.6, 0.84, "tokens", fontsize=12, color=COLORS["gray"])
    save_fig(fig, outpath)


def fig_positional_encoding(outpath):
    n, d = 32, 32
    pos = np.arange(n)[:, None]
    dim = np.arange(d)[None, :]
    angle_rates = 1 / np.power(10000, (2 * (dim // 2)) / d)
    angles = pos * angle_rates
    pe = np.zeros((n, d), dtype=float)
    pe[:, 0::2] = np.sin(angles[:, 0::2])
    pe[:, 1::2] = np.cos(angles[:, 1::2])
    fig, ax = new_fig()
    im = ax.imshow(pe, aspect="auto", cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xlabel("dimension")
    ax.set_ylabel("position")
    ax.set_title("Sinusoidal positional encoding")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_fig(fig, outpath)


def fig_vit_arch(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    add_round_box(ax, (0.1, 0.5), (0.12, 0.1), "Image")
    add_round_box(ax, (0.27, 0.5), (0.16, 0.1), "Patch\nEmbed", text_size=10)
    add_round_box(ax, (0.45, 0.5), (0.14, 0.1), "+ Pos")
    add_round_box(ax, (0.63, 0.5), (0.18, 0.1), "Transformer\nxL", text_size=10)
    add_round_box(ax, (0.8, 0.5), (0.1, 0.1), "CLS")
    add_round_box(ax, (0.92, 0.5), (0.12, 0.1), "Classifier", text_size=10)
    add_arrow(ax, (0.16, 0.5), (0.2, 0.5))
    add_arrow(ax, (0.35, 0.5), (0.38, 0.5))
    add_arrow(ax, (0.52, 0.5), (0.54, 0.5))
    add_arrow(ax, (0.72, 0.5), (0.75, 0.5))
    add_arrow(ax, (0.85, 0.5), (0.86, 0.5))
    save_fig(fig, outpath)


def fig_complexity_chart(outpath):
    n = np.arange(1, 201)
    trans = (n**2) / (n.max() ** 2)
    cnn = n / n.max()
    fig, ax = new_fig()
    ax.plot(n, trans, color=COLORS["red"], label="Transformer O(N^2)")
    ax.plot(n, cnn, color=COLORS["green"], label="CNN proxy O(N)")
    ax.set_xlabel("token count N")
    ax.set_ylabel("relative complexity")
    ax.set_title("Complexity scaling")
    ax.legend()
    save_fig(fig, outpath)


def fig_latency_pipeline(outpath):
    t_pre, t_model, t_post = 5.0, 22.0, 7.0
    total = t_pre + t_model + t_post
    fps = 1000.0 / total
    labels = ["T_pre", "T_model", "T_post", "Total"]
    values = [t_pre, t_model, t_post, total]
    colors = [COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["purple"]]
    fig, ax = new_fig()
    bars = ax.bar(labels, values, color=colors, alpha=0.85)
    ax.set_ylabel("ms")
    ax.set_title("Latency breakdown")
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.8, f"{v:.1f}", ha="center", fontsize=11)
    ax.text(3, total + 3.5, f"FPS={fps:.1f}", ha="center", fontsize=12, color=COLORS["black"])
    save_fig(fig, outpath)


def fig_color_spaces(outpath):
    fig, axes = new_fig(1, 3)
    ax0, ax1, ax2 = axes
    x = np.linspace(0, 1, 256)
    y = np.linspace(0, 1, 256)
    xx, yy = np.meshgrid(x, y)
    rgb = np.stack([xx, yy, np.full_like(xx, 0.2)], axis=-1)
    ax0.imshow(rgb)
    ax0.set_title("RGB plane")
    ax0.set_xticks([])
    ax0.set_yticks([])
    grid = 256
    xv, yv = np.meshgrid(np.linspace(-1, 1, grid), np.linspace(-1, 1, grid))
    r = np.sqrt(xv**2 + yv**2)
    theta = (np.arctan2(yv, xv) + np.pi) / (2 * np.pi)
    s = np.clip(r, 0, 1)
    v = np.ones_like(s)
    hsv_rgb = hsv_to_rgb(theta, s, v)
    hsv_rgb[r > 1] = 1.0
    ax1.imshow(hsv_rgb)
    ax1.set_title("HSV hue")
    ax1.set_xticks([])
    ax1.set_yticks([])
    bar_w = 256
    bar_h = 40
    grad = np.linspace(0, 1, bar_w)
    l_bar = np.stack([grad, grad, grad], axis=-1)
    a_bar = np.stack([grad, 1 - grad, grad], axis=-1)
    b_bar = np.stack([grad, grad, 1 - grad], axis=-1)
    lab_img = np.vstack(
        [
            np.tile(l_bar, (bar_h, 1, 1)),
            np.tile(a_bar, (bar_h, 1, 1)),
            np.tile(b_bar, (bar_h, 1, 1)),
        ]
    )
    ax2.imshow(lab_img)
    ax2.set_title("Lab channels")
    ax2.set_xticks([])
    ax2.set_yticks([bar_h / 2, bar_h * 1.5, bar_h * 2.5])
    ax2.set_yticklabels(["L*", "a*", "b*"])
    save_fig(fig, outpath)


def fig_resampling_aliasing(outpath):
    size = 256
    x = np.linspace(0, 1, size)
    xx = np.tile(x, (size, 1))
    stripes = 0.5 + 0.5 * np.sin(2 * np.pi * xx * 18)
    down = stripes[::4, ::4]
    down_up = resize_nearest(down, (size, size))
    filtered = gaussian_blur(stripes, sigma=1.2)
    down_f = filtered[::4, ::4]
    down_f_up = resize_nearest(down_f, (size, size))
    fig, axes = new_fig(1, 3)
    titles = ["Original", "Naive downsample", "Filtered + downsample"]
    for ax, img, title in zip(axes, [stripes, down_up, down_f_up], titles):
        ax.imshow(img, cmap="gray", vmin=0, vmax=1)
        ax.set_title(title, fontsize=12)
        ax.set_axis_off()
    save_fig(fig, outpath)


def fig_data_augmentation(outpath):
    img, _ = make_color_scene(256)
    flip = np.fliplr(img)
    crop = img[40:220, 40:220]
    crop = resize_nearest(crop, (256, 256))
    jitter = np.clip(img * 1.2 + 0.08, 0, 1)
    fig, axes = new_fig(2, 2)
    titles = ["Original", "Flip", "Crop + resize", "Color jitter"]
    images = [img, flip, crop, jitter]
    for ax, im, title in zip(axes.flatten(), images, titles):
        ax.imshow(im)
        ax.set_title(title, fontsize=12)
        ax.set_axis_off()
    save_fig(fig, outpath)


def fig_cnn_receptive_field(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    origin = (0.06, 0.2)
    cell = 0.06
    draw_grid(ax, origin, 5, 5, cell_size=cell, color=COLORS["gray"], lw=1.0)
    ax.add_patch(
        patches.Rectangle(
            (origin[0] + cell, origin[1] + cell),
            cell * 3,
            cell * 3,
            ec=COLORS["blue"],
            fc=COLORS["blue"],
            alpha=0.2,
            lw=2.0,
        )
    )
    ax.text(0.06, 0.55, "input", fontsize=11, color=COLORS["gray"])
    add_round_box(ax, (0.42, 0.5), (0.12, 0.08), "Conv", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (0.56, 0.5), (0.12, 0.08), "BN", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (0.7, 0.5), (0.12, 0.08), "ReLU", fc="#f6f6f6", text_size=10)
    add_round_box(ax, (0.84, 0.5), (0.12, 0.08), "Pool", fc="#f6f6f6", text_size=10)
    add_arrow(ax, (0.32, 0.5), (0.36, 0.5))
    add_arrow(ax, (0.48, 0.5), (0.5, 0.5))
    add_arrow(ax, (0.62, 0.5), (0.64, 0.5))
    add_arrow(ax, (0.76, 0.5), (0.78, 0.5))
    ax.add_patch(patches.Circle((0.93, 0.5), 0.025, ec=COLORS["black"], fc="white", lw=1.5))
    ax.text(0.93, 0.5, "y", ha="center", va="center", fontsize=10)
    add_arrow(ax, (0.9, 0.5), (0.905, 0.5))
    ax.text(0.62, 0.64, "receptive field grows", fontsize=11, color=COLORS["gray"])
    save_fig(fig, outpath)


def fig_overfitting_regularization(outpath):
    epochs = np.arange(1, 31)
    train = 1.2 * np.exp(-epochs / 12) + 0.1
    val = 1.1 * np.exp(-epochs / 10) + 0.1 + 0.015 * epochs
    train_r = 1.0 * np.exp(-epochs / 10) + 0.12
    val_r = 1.05 * np.exp(-epochs / 9) + 0.15
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    ax0.plot(epochs, train, label="train", color=COLORS["blue"])
    ax0.plot(epochs, val, label="val", color=COLORS["orange"])
    ax0.set_title("Overfitting", fontsize=12)
    ax0.set_xlabel("epoch")
    ax0.set_ylabel("loss")
    ax0.legend()
    ax1.plot(epochs, train_r, label="train", color=COLORS["blue"])
    ax1.plot(epochs, val_r, label="val", color=COLORS["green"])
    ax1.set_title("Regularized", fontsize=12)
    ax1.set_xlabel("epoch")
    ax1.set_ylabel("loss")
    ax1.legend()
    save_fig(fig, outpath)


def fig_det_seg_losses(outpath):
    fig, axes = new_fig(1, 3)
    ax0, ax1, ax2 = axes
    ax0.set_axis_off()
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)
    rect_a = patches.Rectangle((0.15, 0.25), 0.45, 0.5, fc=COLORS["blue"], alpha=0.3, ec=COLORS["blue"])
    rect_b = patches.Rectangle((0.35, 0.35), 0.45, 0.5, fc=COLORS["orange"], alpha=0.3, ec=COLORS["orange"])
    ax0.add_patch(rect_a)
    ax0.add_patch(rect_b)
    ax0.text(0.12, 0.82, "IoU", fontsize=12, color=COLORS["black"])
    p = np.linspace(0.01, 1.0, 200)
    gamma = 2.0
    focal = -((1 - p) ** gamma) * np.log(p)
    ax1.plot(p, focal, color=COLORS["red"])
    ax1.set_title("Focal loss", fontsize=12)
    ax1.set_xlabel("p_t")
    ax1.set_ylabel("loss")
    t = np.linspace(0, 1, 200)
    dice = (2 * t) / (1 + t)
    ax2.plot(t, dice, color=COLORS["green"])
    ax2.set_title("Dice vs overlap", fontsize=12)
    ax2.set_xlabel("overlap")
    ax2.set_ylabel("Dice")
    save_fig(fig, outpath)


def fig_annotation_protocols(outpath):
    img, _ = make_color_scene(256)
    fig, axes = new_fig(1, 2)
    ax0, ax1 = axes
    ax0.imshow(img)
    ax0.set_title("Annotator A/B", fontsize=12)
    ax0.set_axis_off()
    ax0.add_patch(patches.Rectangle((40, 50), 120, 90, fill=False, ec=COLORS["blue"], lw=2.0))
    ax0.add_patch(patches.Rectangle((50, 60), 110, 80, fill=False, ec=COLORS["orange"], lw=2.0, ls="--"))
    ax0.text(42, 45, "A", color=COLORS["blue"], fontsize=10)
    ax0.text(52, 55, "B", color=COLORS["orange"], fontsize=10)
    ax1.set_axis_off()
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    x0, y0, w, h = 0.1, 0.45, 0.8, 0.12
    ax1.add_patch(patches.Rectangle((x0, y0), w * 0.7, h, fc=COLORS["blue"], ec="none", alpha=0.8))
    ax1.add_patch(patches.Rectangle((x0 + w * 0.7, y0), w * 0.15, h, fc=COLORS["orange"], ec="none", alpha=0.8))
    ax1.add_patch(patches.Rectangle((x0 + w * 0.85, y0), w * 0.15, h, fc=COLORS["green"], ec="none", alpha=0.8))
    ax1.text(x0 + w * 0.35, y0 + h / 2, "Train", color="white", ha="center", va="center", fontsize=11)
    ax1.text(x0 + w * 0.775, y0 + h / 2, "Val", color="white", ha="center", va="center", fontsize=11)
    ax1.text(x0 + w * 0.925, y0 + h / 2, "Test", color="white", ha="center", va="center", fontsize=11)
    ax1.set_title("Protocol split", fontsize=12)
    save_fig(fig, outpath)


def fig_vit_training(outpath):
    fig, ax = new_fig()
    ax.set_axis_off()
    add_full_background(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    add_round_box(ax, (0.15, 0.7), (0.2, 0.1), "Pretrain data", text_size=10)
    add_round_box(ax, (0.45, 0.7), (0.18, 0.1), "ViT backbone", text_size=10)
    add_round_box(ax, (0.75, 0.7), (0.2, 0.1), "Finetune data", text_size=10)
    add_round_box(ax, (0.75, 0.4), (0.2, 0.1), "Task head", text_size=10)
    add_arrow(ax, (0.25, 0.7), (0.36, 0.7))
    add_arrow(ax, (0.54, 0.7), (0.65, 0.7))
    add_arrow(ax, (0.75, 0.63), (0.75, 0.47))
    ax.text(0.45, 0.55, "transfer", fontsize=11, color=COLORS["gray"], ha="center")
    save_fig(fig, outpath)


def fig_model_compression(outpath):
    fig, ax = new_fig()
    labels = ["Baseline", "Quantized", "Pruned", "Distilled"]
    latency = np.array([35, 18, 22, 20])
    accuracy = np.array([0.86, 0.83, 0.82, 0.85])
    colors = [COLORS["blue"], COLORS["green"], COLORS["orange"], COLORS["purple"]]
    ax.scatter(latency, accuracy, s=120, c=colors)
    for x, y, label in zip(latency, accuracy, labels):
        ax.text(x + 0.7, y + 0.002, label, fontsize=11)
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Accuracy")
    ax.set_title("Compression trade-offs")
    ax.grid(True, alpha=0.2)
    save_fig(fig, outpath)


def main():
    np.random.seed(SEED)
    apply_style()
    out_dir = Path(__file__).resolve().parent / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    figures = [
        ("cover_bg.png", fig_cover_bg),
        ("cv_taxonomy.png", fig_cv_taxonomy),
        ("pipeline_overview.png", fig_pipeline_overview),
        ("dataset_split.png", fig_dataset_split),
        ("normalization.png", fig_normalization),
        ("histogram.png", fig_histogram),
        ("gaussian_kernel.png", fig_gaussian_kernel),
        ("conv_stride_padding.png", fig_conv_stride_padding),
        ("relu_plot.png", fig_relu_plot),
        ("softmax_plot.png", fig_softmax_plot),
        ("loss_landscape.png", fig_loss_landscape),
        ("confusion_matrix.png", fig_confusion_matrix),
        ("iou_diagram.png", fig_iou_diagram),
        ("pr_curve.png", fig_pr_curve),
        ("map_interp.png", fig_map_interp),
        ("canny_steps.png", fig_canny_steps),
        ("sobel_edges.png", fig_sobel_edges),
        ("contours_before_after.png", fig_contours_before_after),
        ("bbox_overlay.png", fig_bbox_overlay),
        ("yolo_decode.png", fig_yolo_decode),
        ("nms_example.png", fig_nms_example),
        ("attention_matrix.png", fig_attention_matrix),
        ("mha.png", fig_mha),
        ("transformer_block.png", fig_transformer_block),
        ("patchify.png", fig_patchify),
        ("positional_encoding.png", fig_positional_encoding),
        ("vit_arch.png", fig_vit_arch),
        ("complexity_chart.png", fig_complexity_chart),
        ("latency_pipeline.png", fig_latency_pipeline),
        ("color_spaces.png", fig_color_spaces),
        ("resampling_aliasing.png", fig_resampling_aliasing),
        ("data_augmentation.png", fig_data_augmentation),
        ("cnn_receptive_field.png", fig_cnn_receptive_field),
        ("overfitting_regularization.png", fig_overfitting_regularization),
        ("det_seg_losses.png", fig_det_seg_losses),
        ("annotation_protocols.png", fig_annotation_protocols),
        ("vit_training.png", fig_vit_training),
        ("model_compression.png", fig_model_compression),
    ]
    generated = []
    errors = []
    for filename, func in figures:
        outpath = out_dir / filename
        try:
            func(outpath)
            generated.append(str(outpath))
        except Exception as exc:
            errors.append((filename, exc))
    for path in generated:
        print(f"generated: {path}")
    print(f"total: {len(generated)}/{len(figures)}")
    if errors:
        for filename, exc in errors:
            print(f"failed: {filename} -> {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
