import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import random

def create_context_window_figure(seed=7):
    rng = random.Random(seed)

    fig, ax = plt.subplots(figsize=(12, 5))
    horizontal_bar_height = 0.8
    bar_height = horizontal_bar_height

    # Bar 1: Short Prompt
    # Width 100. White (0-90), Gray (90-100)
    ax.add_patch(
        patches.Rectangle(
            (0, 5), 90, horizontal_bar_height, facecolor="white", edgecolor="black", linewidth=1.5
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (90, 5), 10, horizontal_bar_height, facecolor="gray", edgecolor="black", linewidth=1.5
        )
    )
    ax.text(-5, 5.4, "Short prompt", va="center", ha="right", fontsize=12, fontweight="bold")
    ax.annotate(
        "",
        xy=(100, 6.1),
        xytext=(0, 6.1),
        arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.8),
    )
    ax.text(
        50,
        6.25,
        "Context window length",
        va="bottom",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="#333333",
    )
    ax.annotate(
        "Prompt",
        xy=(95, 5.4),
        xytext=(113, 6.9),
        va="center",
        ha="left",
        fontsize=11,
        fontweight="bold",
        color="#333333",
        arrowprops=dict(arrowstyle="->", color="#333333", lw=1.6),
    )

    # Bar 2: RAG Approach
    # Width 100. White (0-50), Orange (50-90) with 9 gaps, Gray (90-100)
    ax.add_patch(
        patches.Rectangle(
            (0, 3), 50, horizontal_bar_height, facecolor="white", edgecolor="black", linewidth=1.5
        )
    )

    # 9 interruptions = 10 chunks in the orange section (width 40)
    gap_orange = 0.5
    chunk_width_orange = (40 - 9 * gap_orange) / 10
    ax.add_patch(
        patches.Rectangle(
            (90, 3), 10, horizontal_bar_height, facecolor="gray", edgecolor="black", linewidth=1.5
        )
    )
    ax.text(-5, 3.4, "RAG approach", va="center", ha="right", fontsize=12, fontweight="bold")

    # Three adjacent green vertical bars from middle-bar bottom to top-bar top.
    middle_bar_bottom = 3.0
    top_bar_top = 5.8
    connector_height = top_bar_top - middle_bar_bottom
    # Make connectors visually readable in slide aspect.
    connector_width = bar_height * 15.0
    connector_start_x = 130.0
    connector_gap = 0.8
    for i in range(3):
        ax.add_patch(
            patches.Rectangle(
                (connector_start_x + i * (connector_width + connector_gap), middle_bar_bottom),
                connector_width,
                connector_height,
                facecolor="#4CAF50",
                edgecolor="black",
                linewidth=1.5,
            )
        )
    connector_group_right_x = connector_start_x + 3 * connector_width + 2 * connector_gap
    ax.text(
        connector_group_right_x + 2.0,
        middle_bar_bottom + connector_height / 2,
        "Document\ndata base",
        va="center",
        ha="left",
        fontsize=12,
        fontweight="bold",
    )

    # Arrow: middle of leftmost vertical bar -> top of orange section in middle horizontal bar.
    left_vertical_mid_x = connector_start_x
    left_vertical_mid_y = middle_bar_bottom + connector_height / 2
    middle_orange_top_x = 70
    middle_orange_top_y = 3 + bar_height
    ax.annotate(
        "",
        xy=(middle_orange_top_x, middle_orange_top_y),
        xytext=(left_vertical_mid_x, left_vertical_mid_y),
        arrowprops=dict(arrowstyle="->", color="#333333", lw=2.0),
    )

    # Add 9 orange slices distributed across vertical green bars (2, 4, 3).
    vertical_slice_counts = [3, 3, 4]
    vertical_slice_gap = 0.08
    max_vertical_slices = max(vertical_slice_counts)
    common_slice_height = (
        connector_height - (max_vertical_slices + 1) * vertical_slice_gap
    ) / 11

    def random_non_overlapping_y_positions(y_start, y_end, n_slices, slice_height):
        if n_slices == 0:
            return []
        span = y_end - y_start
        needed = n_slices * slice_height
        if needed > span:
            raise ValueError("Vertical orange slices do not fit inside connector.")
        free_space = span - needed
        weights = [rng.random() for _ in range(n_slices + 1)]
        weight_sum = sum(weights)
        gaps = [free_space * (w / weight_sum) for w in weights]

        positions = []
        y = y_start + gaps[0]
        for i in range(n_slices):
            positions.append(y)
            y += slice_height
            if i < n_slices - 1:
                y += gaps[i + 1]
        return positions

    for i, n_slices in enumerate(vertical_slice_counts):
        bar_x = connector_start_x + i * (connector_width + connector_gap)
        y_positions = random_non_overlapping_y_positions(
            middle_bar_bottom + vertical_slice_gap,
            top_bar_top - vertical_slice_gap,
            n_slices,
            common_slice_height,
        )
        for y_pos in y_positions:
            ax.add_patch(
                patches.Rectangle(
                    (bar_x, y_pos),
                    connector_width,
                    common_slice_height,
                    facecolor="#FF9800",
                    edgecolor="black",
                    linewidth=1.0,
                )
            )

    curr_x = 50
    for _ in range(10):
        ax.add_patch(
            patches.Rectangle(
                (curr_x, 3),
                chunk_width_orange,
                bar_height,
                facecolor="#FF9800",
                edgecolor="black",
                linewidth=1.5,
            )
        )
        curr_x += chunk_width_orange + gap_orange

    # Bar 3: Full Doc in Context Window
    # Twice as long -> Width 200.
    # White (0-10% -> 0-20), Green (10-95% -> 20-190), Gray (95-100% -> 190-200)
    ax.add_patch(
        patches.Rectangle((0, 1), 20, 0.8, facecolor="white", edgecolor="black", linewidth=1.5)
    )

    # Green context area split into 3 equally long sections
    green_total_width = 170
    green_part_width = green_total_width / 3
    for i in range(3):
        ax.add_patch(
            patches.Rectangle(
                (20 + i * green_part_width, 1),
                green_part_width,
                0.8,
                facecolor="#4CAF50",
                edgecolor="black",
                linewidth=1.5,
            )
        )
    # Draw section dividers above overlays so the 3 parts stay visible.
    for divider_x in (20 + green_part_width, 20 + 2 * green_part_width):
        ax.plot([divider_x, divider_x], [1, 1.8], color="black", linewidth=2.2, zorder=6)

    # Overlay the same number of orange slices as in the RAG bar (10), distributed over green area
    # while avoiding the two section divider positions.
    orange_slices_bottom = 10
    slice_width_bottom = chunk_width_orange
    green_start = 20
    green_end = 190
    padding = 2.0
    divider_margin = 1.0
    divider_1 = 20 + green_part_width
    divider_2 = 20 + 2 * green_part_width

    # Keep bars out of divider zones by using three safe intervals.
    intervals = [
        (green_start + padding, divider_1 - divider_margin),
        (divider_1 + divider_margin, divider_2 - divider_margin),
        (divider_2 + divider_margin, green_end - padding),
    ]
    # Fixed per-section counts ensure all sections are represented.
    section_counts = [3, 3, 4]

    def random_non_overlapping_positions(x_start, x_end, n_slices, width):
        if n_slices == 0:
            return []
        span = x_end - x_start
        needed = n_slices * width
        if needed > span:
            raise ValueError("Orange slices do not fit inside a bottom section interval.")
        free_space = span - needed
        weights = [rng.random() for _ in range(n_slices + 1)]
        gaps = [free_space * (w / sum(weights)) for w in weights]
        positions = []
        x = x_start + gaps[0]
        for i in range(n_slices):
            positions.append(x)
            x += width
            if i < n_slices - 1:
                x += gaps[i + 1]
        return positions

    slice_positions = []
    for (x_start, x_end), count in zip(intervals, section_counts):
        slice_positions.extend(
            random_non_overlapping_positions(x_start, x_end, count, slice_width_bottom)
        )

    for x in slice_positions:
        ax.add_patch(
            patches.Rectangle(
                (x, 1),
                slice_width_bottom,
                bar_height,
                facecolor="#FF9800",
                edgecolor="black",
                linewidth=1.2,
                alpha=0.55,
            )
        )

    ax.add_patch(
        patches.Rectangle((190, 1), 10, 0.8, facecolor="gray", edgecolor="black", linewidth=1.5)
    )
    ax.text(
        -5,
        1.4,
        "Full doc in\ncontext window",
        va="center",
        ha="right",
        fontsize=12,
        fontweight="bold",
    )

    # Formatting for slide readability.
    ax.set_xlim(-60, 210)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    fig.tight_layout()

    return fig, ax


def save_context_window_figure(output_path=None, dpi=200, seed=7):
    if output_path is None:
        output_path = Path(__file__).with_name("context_window_plot.png")
    else:
        output_path = Path(output_path)

    fig, _ = create_context_window_figure(seed=seed)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    saved_to = save_context_window_figure()
    print(f"Saved figure to: {saved_to}")
