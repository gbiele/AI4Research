# Architecture

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

fig, ax = plt.subplots(figsize=(12, 13))
ax.axis('off')

def draw_box(x, y, w, h, title, text="", facecolor="#eef2f5", text_color="#333333"):
    rect = patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.1", 
                                  linewidth=2, edgecolor='#1f77b4', facecolor=facecolor)
    ax.add_patch(rect)
    if text:
        ax.text(x, y + h/5, title, ha='center', va='center', fontsize=14, fontweight='bold', color=text_color)
        ax.text(x, y - h/5, text, ha='center', va='center', fontsize=12, color='#555555')
    else:
        ax.text(x, y, title, ha='center', va='center', fontsize=14, fontweight='bold', color=text_color)

center_x = 6

# Input
draw_box(center_x, 12.0, 6, 0.8, "Input Embeddings + Positional Encoding", "Converts raw tokens to dense vectors with position context")

# Transformer Block
block_y_center = 7.5
block_h = 6.5
block_rect = patches.FancyBboxPatch((center_x - 5, block_y_center - block_h/2), 10, block_h, 
                                    boxstyle="round,pad=0.1", linewidth=2, edgecolor='#2ca02c', 
                                    facecolor='#fafdfa', linestyle='--')
ax.add_patch(block_rect)
ax.text(center_x - 4.8, block_y_center + block_h/2 - 0.4, "Transformer Block (Repeated N times)", 
        ha='left', va='top', fontsize=14, fontweight='bold', color='#2ca02c')

# Inside Block
draw_box(center_x, 9.5, 6, 1.0, "Multi-Head Attention (MHA)", "Contextual Weighting\nDetermines relevance of prior tokens via Q, K, V matrices")
ax.text(
    10.4,
    9.5,
    "Main purpose:\nChooses which past\nwords/tokens matter\nmost for next-token\nprediction",
    ha='left',
    va='center',
    fontsize=11,
    color="#333333",
)

draw_box(center_x, 7.5, 5, 0.8, "MoE Router Network", "Sparse Activation: Routes token to top-k experts")

# Experts
draw_box(center_x - 3, 5.5, 2.2, 1.2, "Expert 1\n(Sub-FFN)", "Active\n(Key-Value Memory)", facecolor="#d6e8d5")
draw_box(center_x, 5.5, 2.2, 1.2, "Expert 2\n(Sub-FFN)", "Inactive\n(Bypassed)", facecolor="#f2dede")
draw_box(center_x + 3, 5.5, 2.2, 1.2, "Expert N\n(Sub-FFN)", "Active\n(Key-Value Memory)", facecolor="#d6e8d5")

ax.text(center_x, 4.5, "Mixture of Experts (MoE) Layer", 
        ha='center', va='center', fontsize=12, style='italic', color="#555555")
ax.text(
    10.4,
    5.5,
    "Main purpose (FFN):\nTransforms context into\nhigher-level patterns\n('working memory' for\nwhat to generate next)",
    ha='left',
    va='center',
    fontsize=11,
    color="#333333",
)

# Output
draw_box(center_x, 2.0, 6, 1.0, "Output Head (Linear + Softmax)", "Objective: Minimize Cross-Entropy Loss\n(Next-Token Prediction interpolation)")

# Arrows
def draw_arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=2, color="#777777"))

draw_arrow(center_x, 12.0 - 0.4, center_x, 9.5 + 0.5)
draw_arrow(center_x, 9.5 - 0.5, center_x, 7.5 + 0.4)

# Router to experts
draw_arrow(center_x, 7.5 - 0.4, center_x - 3, 5.5 + 0.6)
draw_arrow(center_x, 7.5 - 0.4, center_x, 5.5 + 0.6)
draw_arrow(center_x, 7.5 - 0.4, center_x + 3, 5.5 + 0.6)

# Experts to Output Head
draw_arrow(center_x - 3, 5.5 - 0.6, center_x, 2.0 + 0.5)
draw_arrow(center_x, 5.5 - 0.6, center_x, 2.0 + 0.5)
draw_arrow(center_x + 3, 5.5 - 0.6, center_x, 2.0 + 0.5)

plt.xlim(0, 12)
plt.ylim(0.5, 13)
plt.tight_layout()
def save_llm_architecture_figure(output_path=None, dpi=200):
    if output_path is None:
        output_path = Path(__file__).with_name("LLM_architecture.png")
    else:
        output_path = Path(output_path)

    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    saved_to = save_llm_architecture_figure()
    print(f"Saved figure to: {saved_to}")