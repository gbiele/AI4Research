import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path


def setup_ax(ax, xlim, ylim):
    ax.axis("off")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)


def draw_mini_llm_icon(ax, x, y, width=2.45, height=1.25):
    # Outer architecture block.
    outer_y_shift = height * 0.10
    outer = patches.FancyBboxPatch(
        (x - width / 2, y - height / 2 + outer_y_shift),
        width,
        height,
        boxstyle="round,pad=0.08",
        linewidth=1.2,
        edgecolor="#d62728",
        facecolor="#f0fdf4",
    )
    ax.add_patch(outer)

    # Thin inner boxes with slight offset to suggest repeated internal layers.
    inner_w = width * 0.84
    inner_h = height * 0.66
    base_x = x - width / 2 + width * 0.06
    base_y = y - height / 2 + height * 0.10 + outer_y_shift
    inner_shift_x = width * 0.04
    inner_shift_y = height * 0.035
    for i in (2, 1, 0):
        inner = patches.FancyBboxPatch(
            (base_x + i * inner_shift_x, base_y - i * inner_shift_y),
            inner_w,
            inner_h,
            boxstyle="round,pad=0.04",
            linewidth=0.8,
            edgecolor="#2ca02c",
            facecolor="#e6f7ea",
            alpha=0.85 if i > 0 else 0.95,
        )
        ax.add_patch(inner)

    # Simple internal sketch: one MHA -> FFN block pair
    inner_h = height * 0.20
    inner_w = width * 0.34
    left_x = x - width * 0.38
    right_x = x + width * 0.04
    inner_y = y + height * 0.05

    mha = patches.FancyBboxPatch(
        (left_x, inner_y - inner_h / 2),
        inner_w,
        inner_h,
        boxstyle="round,pad=0.02",
        linewidth=1.0,
        edgecolor="#1f77b4",
        facecolor="#e1f5fe",
    )
    ffn = patches.FancyBboxPatch(
        (right_x, inner_y - inner_h / 2),
        inner_w,
        inner_h,
        boxstyle="round,pad=0.02",
        linewidth=1.0,
        edgecolor="#ff7f0e",
        facecolor="#fff3e0",
    )
    ax.add_patch(mha)
    ax.add_patch(ffn)
    ax.text(left_x + inner_w / 2, inner_y, "MHA", ha="center", va="center", fontsize=6.8, fontweight="bold")
    ax.text(right_x + inner_w / 2, inner_y, "FFN", ha="center", va="center", fontsize=6.8, fontweight="bold")
    ax.annotate(
        "",
        xy=(right_x - 0.02, inner_y),
        xytext=(left_x + inner_w + 0.02, inner_y),
        arrowprops=dict(arrowstyle="->", lw=1.0, color="#666666"),
    )
    ax.text(x, y + height * 0.50, "LLM", ha="center", va="center", fontsize=9, fontweight="bold", color="#166534")


def draw_pretraining(ax):
    setup_ax(ax, (0, 12), (0.5, 8))

    corpus_text = "The capital of France is Paris and the..."
    rect_corpus = patches.FancyBboxPatch(
        (0.5, 6.5),
        11,
        1.2,
        boxstyle="round,pad=0.1",
        linewidth=2,
        edgecolor="#777777",
        facecolor="#f9f9f9",
    )
    ax.add_patch(rect_corpus)
    ax.text(
        6,
        7.3,
        "Large Text Corpus (Trillions of Tokens)",
        ha="center",
        fontsize=12,
        fontweight="bold",
    )
    ax.text(
        6,
        6.8,
        f'"... {corpus_text} ..."',
        ha="center",
        fontsize=14,
        family="monospace",
        color="#444444",
    )

    tokens = ["The", "capital", "of", "France", "is"]
    target = "Paris"
    for i, token in enumerate(tokens):
        rect = patches.Rectangle(
            (1.5 + i * 1.5, 5.0),
            1.2,
            0.6,
            linewidth=1,
            edgecolor="#1f77b4",
            facecolor="#e1f5fe",
        )
        ax.add_patch(rect)
        ax.text(2.1 + i * 1.5, 5.3, token, ha="center", va="center", fontsize=11)

    ax.text(6, 4.7, "Input Sequence (Context Window)", ha="center", fontsize=10, fontweight="bold")

    rect_model = patches.FancyBboxPatch(
        (2, 2.5),
        8,
        1.5,
        boxstyle="round,pad=0.2",
        linewidth=2,
        edgecolor="#2ca02c",
        facecolor="#f0fdf4",
    )
    ax.add_patch(rect_model)
    draw_mini_llm_icon(ax, x=5.0, y=3.25)
    ax.text(
        6.5,
        3.25,
        "Weights updated to correctly\npredict the next token\nin the pre-training corpus",
        ha="left",
        va="center",
        fontsize=16,
        color="#166534",
        fontweight="bold",
    )

    rect_out = patches.Rectangle(
        (4.5, 1.0), 3, 0.8, linewidth=1, edgecolor="#d62728", facecolor="#fef2f2"
    )
    ax.add_patch(rect_out)
    ax.text(6, 1.5, "Probability Distribution", ha="center", fontsize=10, fontweight="bold")
    ax.text(6, 1.2, "Paris: 0.92 | London: 0.03 | ...", ha="center", fontsize=9)

    ax.text(9.5, 1.4, f"Target: '{target}'", fontsize=11, fontweight="bold", color="#d62728")
    ax.annotate(
        "",
        xy=(7.6, 1.4),
        xytext=(8.8, 1.4),
        arrowprops=dict(arrowstyle="<->", color="#d62728"),
    )
    ax.text(
        10.5,
        1.0,
        "Cross-Entropy Loss\n(Minimize Prediction Error)",
        ha="center",
        fontsize=9,
        color="#d62728",
    )

    ax.annotate("", xy=(6, 5.7), xytext=(6, 6.4), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))
    ax.annotate("", xy=(6, 4.1), xytext=(6, 4.9), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))
    ax.annotate("", xy=(6, 1.9), xytext=(6, 2.4), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))


def draw_sft(ax):
    setup_ax(ax, (0, 12), (0, 9.5))

    rect_data = patches.FancyBboxPatch(
        (1.5, 7.0),
        9,
        2.0,
        boxstyle="round,pad=0.1",
        linewidth=2,
        edgecolor="#9467bd",
        facecolor="#f3e9f6",
    )
    ax.add_patch(rect_data)
    ax.text(
        6,
        8.6,
        "Supervised Fine-Tuning (SFT) Dataset",
        ha="center",
        fontsize=12,
        fontweight="bold",
        color="#4a148c",
    )
    ax.text(
        6,
        8.2,
        "High-quality, human-curated (Prompt, Response) pairs",
        ha="center",
        fontsize=11.5,
        style="italic",
    )

    ax.text(2.5, 7.7, "Prompt:", ha="right", fontsize=11, fontweight="bold")
    ax.text(2.7, 7.7, '"Explain gravity briefly."', ha="left", fontsize=11, family="monospace")
    ax.text(2.5, 7.2, "Response:", ha="right", fontsize=11, fontweight="bold", color="#2ca02c")
    ax.text(
        2.7,
        7.2,
        '"Gravity is a fundamental force that..."',
        ha="left",
        fontsize=11,
        family="monospace",
        color="#2ca02c",
    )

    rect_input = patches.FancyBboxPatch(
        (2.5, 5.0),
        7,
        0.8,
        boxstyle="round,pad=0.1",
        linewidth=1.5,
        edgecolor="#1f77b4",
        facecolor="#e1f5fe",
    )
    ax.add_patch(rect_input)
    ax.text(
        6,
        5.4,
        "[USER] Explain gravity briefly. [ASSISTANT]",
        ha="center",
        va="center",
        fontsize=11,
        family="monospace",
    )
    ax.text(6, 4.6, "Input Sequence (Formatted Prompt)", ha="center", fontsize=10, fontweight="bold")

    rect_model = patches.FancyBboxPatch(
        (2, 2.5),
        8,
        1.5,
        boxstyle="round,pad=0.2",
        linewidth=2,
        edgecolor="#2ca02c",
        facecolor="#f0fdf4",
    )
    ax.add_patch(rect_model)
    draw_mini_llm_icon(ax, x=5.0, y=3.25)
    ax.text(
        6.5,
        3.25,
        "Weights updated to match\ncurated responses",
        ha="left",
        va="center",
        fontsize=16,
        color="#166534",
        fontweight="bold",
    )

    rect_pred = patches.Rectangle(
        (2.5, 1.0), 3.0, 0.8, linewidth=1, edgecolor="#d62728", facecolor="#fef2f2"
    )
    ax.add_patch(rect_pred)
    ax.text(4.0, 1.4, "Predicted Tokens\n(Distribution)", ha="center", va="center", fontsize=10)

    rect_target = patches.Rectangle(
        (6.5, 1.0), 3.0, 0.8, linewidth=1, edgecolor="#2ca02c", facecolor="#e8f5e9"
    )
    ax.add_patch(rect_target)
    ax.text(8.0, 1.4, 'Target Tokens\n("Gravity is a...")', ha="center", va="center", fontsize=10, color="#166534")

    ax.annotate(
        "",
        xy=(5.6, 1.4),
        xytext=(6.4, 1.4),
        arrowprops=dict(arrowstyle="<->", color="#d62728", lw=2),
    )
    ax.text(
        6.0,
        0.7,
        "Supervised Cross-Entropy Loss\n(Penalize deviation from curated response)",
        ha="center",
        fontsize=10,
        color="#d62728",
    )

    ax.annotate("", xy=(6, 5.9), xytext=(6, 6.9), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))
    ax.annotate("", xy=(6, 4.2), xytext=(6, 4.5), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))
    ax.annotate("", xy=(4.0, 1.9), xytext=(4.0, 2.4), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))
    ax.annotate(
        "",
        xy=(8.0, 1.9),
        xytext=(8.0, 6.9),
        arrowprops=dict(
            arrowstyle="->",
            lw=1.5,
            color="#2ca02c",
            linestyle="--",
            connectionstyle="arc3,rad=-0.3",
        ),
    )
    ax.text(9.2, 4.5, "Target Response\nData flows to\nLoss Calculation", ha="left", va="center", fontsize=9, color="#2ca02c")


def draw_box(ax, x, y, w, h, title, text="", facecolor="#eef2f5", text_color="#333333", edgecolor="#1f77b4", linestyle="-", alpha=1.0):
    rect = patches.FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle="round,pad=0.1",
        linewidth=2,
        edgecolor=edgecolor,
        facecolor=facecolor,
        linestyle=linestyle,
        alpha=alpha,
    )
    ax.add_patch(rect)
    if text:
        ax.text(x, y + h / 6, title, ha="center", va="center", fontsize=12, fontweight="bold", color=text_color)
        ax.text(x, y - h / 5, text, ha="center", va="center", fontsize=10, color="#555555")
    else:
        ax.text(x, y, title, ha="center", va="center", fontsize=12, fontweight="bold", color=text_color)


def draw_rlhf(ax):
    setup_ax(ax, (0, 12), (0, 10))

    rect_data = patches.FancyBboxPatch(
        (0.5, 4.5),
        11,
        5.0,
        boxstyle="round,pad=0.1",
        linewidth=2,
        edgecolor="#9467bd",
        facecolor="#f9f4fa",
        linestyle="--",
    )
    ax.add_patch(rect_data)
    ax.text(
        6,
        9.2,
        "Human Preference Dataset",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#4a148c",
    )
    ax.text(
        6,
        8.8,
        "Millions of these records are collected to train the models",
        ha="center",
        va="center",
        fontsize=11,
        color="#555",
        style="italic",
    )

    draw_box(ax, 6, 8.2, 6, 0.8, "1. User Prompt", '"Write a polite email declining an invitation"', facecolor="#e1f5fe", edgecolor="#1f77b4")
    draw_box(
        ax,
        3.5,
        6.4,
        4.5,
        1.0,
        "2. Response A (Model Generated)",
        '"Thank you for the invite, but I am\nunable to attend at this time..."',
        facecolor="#ffffff",
        edgecolor="#ccc",
    )
    draw_box(ax, 8.5, 6.4, 4.5, 1.0, "3. Response B (Model Generated)", '"No, I won\'t come."', facecolor="#ffffff", edgecolor="#ccc")
    draw_box(
        ax,
        6,
        5.0,
        5,
        0.8,
        "4. Human Preference Label",
        "Rater explicitly marks: Output A is better than Output B",
        facecolor="#fff3e0",
        edgecolor="#ff7f0e",
    )

    ax.text(3.5, 6.9, "[Preferred]", ha="center", va="center", fontsize=10, fontweight="bold", color="#2ca02c")
    ax.text(8.5, 6.9, "[Rejected]", ha="center", va="center", fontsize=10, fontweight="bold", color="#d62728")
    ax.annotate("", xy=(4.5, 7.2), xytext=(6, 7.7), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))
    ax.annotate("", xy=(7.5, 7.2), xytext=(6, 7.7), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))

    draw_box(
        ax,
        6,
        2.8,
        8,
        1.2,
        "Step 1: Train Reward Model on the Data",
        "Learns to mathematically score responses based on the human labels.\n(E.g., learns to assign Response A: +2.5, Response B: -1.0)",
        facecolor="#fff3e0",
        edgecolor="#ff7f0e",
    )
    draw_box(
        ax,
        6,
        1.0,
        9,
        1.2,
        "",
        "",
        facecolor="#f0fdf4",
        edgecolor="#2ca02c",
    )
    draw_mini_llm_icon(ax, x=5.0, y=0.9, width=2.25, height=1.0)
    ax.text(
        7.4,
        1.0,
        "Policy weights updated\nusing reward scores",
        ha="left",
        va="center",
        fontsize=16,
        color="#166534",
        fontweight="bold",
    )

    ax.annotate("", xy=(6, 3.5), xytext=(6, 4.5), arrowprops=dict(arrowstyle="->", lw=3, color="#777"))
    ax.text(6.2, 4.0, "Feeds into", ha="left", color="#777", fontweight="bold")
    ax.annotate("", xy=(6, 1.7), xytext=(6, 2.1), arrowprops=dict(arrowstyle="->", lw=3, color="#777"))
    ax.text(6.2, 1.9, "Guides", ha="left", color="#777", fontweight="bold")


def draw_rlvf(ax):
    setup_ax(ax, (0, 12), (0, 10))

    rect_data = patches.FancyBboxPatch(
        (0.5, 4.5),
        11,
        5.0,
        boxstyle="round,pad=0.1",
        linewidth=2,
        edgecolor="#17becf",
        facecolor="#f0fbfb",
        linestyle="--",
    )
    ax.add_patch(rect_data)
    ax.text(
        6,
        9.2,
        "Verifiable Tasks (Math, Code, Logic)",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#008b8b",
    )
    ax.text(
        6,
        8.8,
        "Tasks where the answer is objectively right or wrong, requiring System 2 reasoning",
        ha="center",
        va="center",
        fontsize=11,
        color="#555",
        style="italic",
    )

    draw_box(ax, 6, 8.2, 6, 0.8, "1. User Prompt", '"Write a Python function to sort an array"', facecolor="#e1f5fe", edgecolor="#1f77b4")
    draw_box(
        ax,
        3.5,
        6.4,
        4.5,
        1.0,
        "2. Reasoning Path A (Model)",
        "def sort(arr):\n    return sorted(arr)\n# [Outputs correct logic]",
        facecolor="#ffffff",
        edgecolor="#ccc",
    )
    draw_box(
        ax,
        8.5,
        6.4,
        4.5,
        1.0,
        "3. Reasoning Path B (Model)",
        "def sort(arr):\n    return arr[0]\n# [Outputs flawed logic]",
        facecolor="#ffffff",
        edgecolor="#ccc",
    )
    draw_box(
        ax,
        6,
        5.0,
        7,
        0.8,
        "4. Objective Verifier / Environment",
        "Python Compiler & Unit Tests run the generated code",
        facecolor="#e6f2ff",
        edgecolor="#0052cc",
    )

    ax.text(3.5, 7.0, "[Execution Success]", ha="center", va="center", fontsize=10, fontweight="bold", color="#2ca02c")
    ax.text(8.5, 7.0, "[Execution Error]", ha="center", va="center", fontsize=10, fontweight="bold", color="#d62728")
    ax.annotate("", xy=(4.5, 7.2), xytext=(6, 7.7), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))
    ax.annotate("", xy=(7.5, 7.2), xytext=(6, 7.7), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))
    ax.annotate("", xy=(5, 5.4), xytext=(4.5, 6.2), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))
    ax.annotate("", xy=(7, 5.4), xytext=(7.5, 6.2), arrowprops=dict(arrowstyle="->", lw=2, color="#aaa"))

    draw_box(
        ax,
        6,
        2.8,
        8,
        1.2,
        "Step 1: Deterministic Reward Assignment",
        "No human raters. The environment returns an absolute signal.\n(Path A: All tests pass = +1.0 Reward | Path B: Test failed = -1.0 Reward)",
        facecolor="#fff3e0",
        edgecolor="#ff7f0e",
    )
    draw_box(
        ax,
        6,
        1.0,
        9,
        1.2,
        "",
        "",
        facecolor="#f0fdf4",
        edgecolor="#2ca02c",
    )
    draw_mini_llm_icon(ax, x=5.0, y=0.9, width=2.25, height=1.0)
    ax.text(
        7,
        1,
        "Policy weights updated to\nmaximize verifier success",
        ha="left",
        va="center",
        fontsize=16,
        color="#166534",
        fontweight="bold",
    )

    ax.annotate("", xy=(6, 3.5), xytext=(6, 4.5), arrowprops=dict(arrowstyle="->", lw=3, color="#777"))
    ax.text(6.2, 4.0, "Absolute Signal flows to", ha="left", color="#777", fontweight="bold")
    ax.annotate("", xy=(6, 1.7), xytext=(6, 2.1), arrowprops=dict(arrowstyle="->", lw=3, color="#777"))
    ax.text(6.2, 1.9, "Guides", ha="left", color="#777", fontweight="bold")


def save_stage(draw_fn, output_path, figsize, dpi=200):
    fig, ax = plt.subplots(figsize=figsize)
    draw_fn(ax)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def save_llm_training_figures(output_dir=None, dpi=200):
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_specs = [
        ("Pretraining", draw_pretraining, (12, 8), output_dir / "LLM_training_pretraining.png"),
        ("SFT", draw_sft, (12, 9), output_dir / "LLM_training_sft.png"),
        ("RLHF", draw_rlhf, (12, 10), output_dir / "LLM_training_rlhf.png"),
        ("RLVF", draw_rlvf, (12, 10), output_dir / "LLM_training_rlvf.png"),
    ]

    for _, draw_fn, figsize, stage_path in stage_specs:
        save_stage(draw_fn, stage_path, figsize, dpi=dpi)

    large_fig, axes = plt.subplots(1, 4, figsize=(48, 10))
    draw_fns = [draw_pretraining, draw_sft, draw_rlhf, draw_rlvf]
    labels = ["Pretraining", "SFT", "RLHF", "RLVF"]
    for ax, draw_fn, label in zip(axes, draw_fns, labels):
        draw_fn(ax)
        ax.set_title(label, fontsize=20, fontweight="bold", pad=18)
    large_fig.tight_layout()
    combined_path = output_dir / "LLM_training_all_stages.png"
    large_fig.savefig(combined_path, dpi=dpi, bbox_inches="tight")
    plt.close(large_fig)

    return {
        "pretraining": stage_specs[0][3],
        "sft": stage_specs[1][3],
        "rlhf": stage_specs[2][3],
        "rlvf": stage_specs[3][3],
        "combined": combined_path,
    }


if __name__ == "__main__":
    saved_paths = save_llm_training_figures()
    for name, path in saved_paths.items():
        print(f"{name}: {path}")