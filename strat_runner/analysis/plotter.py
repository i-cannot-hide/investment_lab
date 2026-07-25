from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from enum import Enum

from engine.journal import EntryType

# Single legend so entry symbols toggle on click. Plotly's secondary legends
# (legend2) have historically broken / inconsistent itemclick behavior.
SERIES_LEGEND = "legend"

# Plotly cannot natively "toggle whole group on parent click, item on child
# click". This hook makes a series-line legend click hide/show that series'
# entry markers too; entry clicks keep default per-item toggle.
# Also reapplies marker y_shift_px (screen pixels) after plot/zoom — scatter
# has no pixel offset API, and SVG path tricks get re-centered by Plotly.
_SERIES_LEGEND_CLICK_SCRIPT = """
var gd = document.getElementById('{plot_id}');
if (!gd || gd._seriesLegendHooked) return;
gd._seriesLegendHooked = true;

function applyMarkerPixelOffsets(gd) {
  if (gd._buyOffsetApplying) return;
  var yaxis = gd._fullLayout && gd._fullLayout.yaxis;
  if (!yaxis || !yaxis.d2l || !yaxis.l2p || !yaxis.p2l || !yaxis.l2d) return;
  var rangeKey = JSON.stringify(yaxis.range);
  if (gd._buyOffsetRangeKey === rangeKey) return;
  var indices = [];
  var ys = [];
  gd.data.forEach(function(t, i) {
    if (!t.meta || !t.meta.y_shift_px) return;
    if (!t._baseY) {
      t._baseY = (t.y || []).slice();
    }
    var shift = t.meta.y_shift_px;
    var newY = t._baseY.map(function(yv) {
      if (yv === null || yv === undefined) return yv;
      var p = yaxis.l2p(yaxis.d2l(yv));
      return yaxis.l2d(yaxis.p2l(p + shift));
    });
    indices.push(i);
    ys.push(newY);
  });
  if (!indices.length) return;
  gd._buyOffsetApplying = true;
  gd._buyOffsetRangeKey = rangeKey;
  Plotly.restyle(gd, {y: ys}, indices).then(function() {
    gd._buyOffsetApplying = false;
  });
}

gd.on('plotly_legendclick', function(e) {
  var t = gd.data[e.curveNumber];
  if (!t || !t.meta || t.meta.role !== 'series') {
    return;
  }
  var series = t.meta.series;
  var hiding = (t.visible !== false && t.visible !== 'legendonly');
  var next = hiding ? 'legendonly' : true;
  var indices = [];
  for (var i = 0; i < gd.data.length; i++) {
    var d = gd.data[i];
    if (d.meta && d.meta.series === series) {
      indices.push(i);
    }
  }
  if (!indices.length) return;
  Plotly.restyle(gd, {visible: next}, indices);
  return false;
});

gd.on('plotly_afterplot', function() {
  applyMarkerPixelOffsets(gd);
});
applyMarkerPixelOffsets(gd);
"""

_USD_SERIES_COLUMNS = {
    "equity",
    "available_usd",
    "frozen_usd",
    "total_usd",
}


class Scale(Enum):
    LOG = "log"
    LINEAR = "linear"

_MARKER_STYLE = {
    EntryType.ORDER_FILLED.value: {
        "BUY": {
            "name": "buy",
            "symbol": "triangle-up",
            # Scatter markers are centered on the point; nudge the glyph down
            # by half the marker size in screen pixels (size 10 → 5px).
            "y_shift_px": 5,
            "color": "#00c853",
            "size": 10,
            "line_color": "#000000",
            "line_width": 1,
            "hover": "BUY",
        },
        "SELL": {
            "name": "sell",
            "symbol": "triangle-down",
            "color": "#d62728",
            "size": 10,
            "line_color": "#000000",
            "line_width": 1,
            "hover": "SELL",
        },
    },
    EntryType.ORDER_CANCELLED.value: {
        "name": "cancel",
        "symbol": "x",
        "color": "#7f7f7f",
        "size": 10,
        "hover": "CANCEL",
    },
    EntryType.DEPOSIT.value: {
        "name": "deposit",
        "symbol": "line-nw",
        "color": "#1b5e20",
        "size": 10,
        "line_color": "#1b5e20",
        "line_width": 2,
        "hover": "DEPOSIT",
    },
    EntryType.INTEREST.value: {
        "name": "interest",
        "symbol": "line-nw",
        "color": "#2e7d32",
        "size": 6,
        "line_color": "#2e7d32",
        "line_width": 2,
        "hover": "INTEREST",
    },
    EntryType.WITHDRAWAL.value: {
        "name": "withdrawal",
        "symbol": "line-ne",
        "color": "#8b0000",
        "size": 10,
        "line_color": "#8b0000",
        "line_width": 1,
        "hover": "WITHDRAWAL",
    },
    EntryType.IS_ATH.value: {
        "name": "ath",
        "symbol": "diamond",
        "color": "#f9a825",
        "size": 8,
        "line_color": "#f57f17",
        "line_width": 1,
        "hover": "ATH",
    },
}

_AGGREGATE_STYLE = {
    "name": "events",
    "symbol": "circle",
    "color": "#455a64",
    "size": 10,
    "line_color": "#000000",
    "line_width": 1,
    "hover": "EVENTS",
}

# Relative y stagger so same-timestamp markers stay visible together.
_STACK_Y_FRAC = 0.03


def flatten_journal(steps: pd.DataFrame) -> pd.DataFrame:
    """Explode step `journal` lists into one row per entry."""
    rows: list[dict] = []
    frame = steps.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    for _, step in frame.iterrows():
        for entry in step.get("journal") or []:
            rows.append({"time": step["time"], **entry})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _entry_type_values(journal: list[EntryType] | None) -> list[str]:
    if not journal:
        return []
    return [
        entry.value if isinstance(entry, EntryType) else str(entry) for entry in journal
    ]


def _marker_y(entry: pd.Series, frame: pd.DataFrame, column: str) -> float | None:
    """Y for a journal marker on the plotted series."""
    if (
        entry.get("type") == EntryType.ORDER_FILLED.value
        and column in {"price", "high", "low", "open", "close", "level"}
        and entry.get("price") is not None
        and pd.notna(entry.get("price"))
    ):
        return float(entry["price"])

    match = frame.loc[frame["time"] == entry["time"], column]
    if match.empty or pd.isna(match.iloc[0]):
        return None
    return float(match.iloc[0])


def _is_ath_true(entry: pd.Series) -> bool:
    value = entry.get("IsATH")
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def _style_for_entry(entry: pd.Series) -> dict | None:
    entry_type = entry.get("type")
    if entry_type == EntryType.IS_ATH.value and not _is_ath_true(entry):
        return None
    style = _MARKER_STYLE.get(entry_type)
    if style is None:
        return _AGGREGATE_STYLE
    if entry_type == EntryType.ORDER_FILLED.value:
        return style.get(entry.get("side"), _AGGREGATE_STYLE)
    return style


def _format_number(value, *, max_decimals: int) -> str:
    """Format a number with at most ``max_decimals`` places (trim trailing zeros)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    quantized = Decimal(str(value)).quantize(
        Decimal("1").scaleb(-max_decimals),
        rounding=ROUND_HALF_UP,
    )
    text = f"{quantized:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _format_asset_amount(value, *, asset: str | None) -> str:
    """USD → 2 dp max; everything else (coins, prices) → 4 dp max."""
    max_decimals = 2 if (asset or "").upper() == "USD" else 4
    return _format_number(value, max_decimals=max_decimals)


def _series_y_hover_format(column: str) -> str:
    if column in _USD_SERIES_COLUMNS or column.endswith("_usd"):
        return ",.2f"
    return ",.4f"


def _hover_line(entry: pd.Series) -> str:
    entry_type = entry.get("type")
    if entry_type == EntryType.ORDER_FILLED.value:
        side = entry.get("side") or "?"
        qty = entry.get("quantity")
        price = entry.get("price")
        ticker = entry.get("ticker") or ""
        parts = [str(side)]
        if ticker:
            parts.append(str(ticker))
        if qty is not None and pd.notna(qty):
            parts.append(_format_asset_amount(qty, asset=ticker))
        if price is not None and pd.notna(price):
            # Fill prices are quote currency levels; keep 4 dp like other non-USD.
            parts.append(f"@ {_format_number(price, max_decimals=4)}")
        body = " ".join(parts)
    elif entry_type == EntryType.ORDER_CANCELLED.value:
        body = f"CANCEL {entry.get('order_id') or ''}".strip()
    elif entry_type == EntryType.DEPOSIT.value:
        currency = entry.get("currency") or ""
        amount = _format_asset_amount(entry.get("amount"), asset=currency)
        body = f"DEPOSIT {amount} {currency}".strip()
    elif entry_type == EntryType.INTEREST.value:
        ticker = entry.get("ticker") or ""
        amount = _format_asset_amount(entry.get("amount"), asset=ticker)
        body = f"INTEREST {amount} {ticker}".strip()
    elif entry_type == EntryType.WITHDRAWAL.value:
        currency = entry.get("currency") or ""
        amount = _format_asset_amount(entry.get("amount"), asset=currency)
        body = f"WITHDRAWAL {amount} {currency}".strip()
    elif entry_type == EntryType.IS_ATH.value:
        ticker = entry.get("ticker") or ""
        label = "ATH" if _is_ath_true(entry) else "not ATH"
        body = f"{label} {ticker}".strip()
    else:
        body = str(entry_type or "event")

    experiment = entry.get("experiment")
    if experiment is not None and pd.notna(experiment) and str(experiment):
        return f"{experiment}: {body}"
    return body


def _stack_marker_y(base_y: float, index: int, count: int) -> float:
    """Spread same-timestamp markers vertically around ``base_y``."""
    if count <= 1 or base_y == 0:
        return base_y
    center = (count - 1) / 2
    return base_y * (1 + _STACK_Y_FRAC * (index - center))


def aggregate_journal_markers(
    journal: pd.DataFrame,
    frame: pd.DataFrame,
    column: str,
) -> list[dict]:
    """Build one marker per journal entry.

    Same-timestamp entries keep their individual styles and are staggered in y
    so every marker stays visible.
    """
    if journal.empty:
        return []

    markers: list[dict] = []
    ordered = journal.sort_values("time", kind="mergesort")
    for time, group in ordered.groupby("time", sort=True):
        rows = [
            row
            for _, row in group.iterrows()
            if _style_for_entry(row) is not None
        ]
        if not rows:
            continue

        prepared: list[tuple[pd.Series, float, dict]] = []
        for entry in rows:
            y = _marker_y(entry, frame, column)
            style = _style_for_entry(entry)
            if y is None or style is None:
                continue
            prepared.append((entry, y, style))

        count = len(prepared)
        for index, (entry, y, style) in enumerate(prepared):
            experiment = entry.get("experiment")
            series = (
                str(experiment)
                if experiment is not None
                and not (isinstance(experiment, float) and pd.isna(experiment))
                and str(experiment)
                else None
            )
            markers.append(
                {
                    "time": time,
                    "y": _stack_marker_y(y, index, count),
                    "style": style,
                    "text": "",
                    "hover": _hover_line(entry),
                    "count": 1,
                    "series": series,
                }
            )
    return markers


def series_journal_customdata(
    times,
    markers: list[dict],
) -> list[str]:
    """Per-timestamp hover suffix for the series line (empty if no entries)."""
    by_time: dict[pd.Timestamp, list[str]] = {}
    for marker in markers:
        by_time.setdefault(pd.Timestamp(marker["time"]), []).append(marker["hover"])

    customdata: list[str] = []
    for time in times:
        lines = by_time.get(pd.Timestamp(time))
        if not lines:
            customdata.append("")
            continue
        customdata.append("<br>" + "<br>".join(lines))
    return customdata


def _add_journal_traces(
    fig: go.Figure,
    markers: list[dict],
    *,
    series: str,
):
    """Draw journal markers for one series under that series' legend group."""
    if not markers:
        return

    by_name: dict[str, list[dict]] = {}
    for marker in markers:
        by_name.setdefault(marker["style"]["name"], []).append(marker)

    for entry_name, group in by_name.items():
        style = group[0]["style"]
        fig.add_trace(
            go.Scatter(
                x=[marker["time"] for marker in group],
                y=[marker["y"] for marker in group],
                mode="markers",
                name=entry_name,
                legend=SERIES_LEGEND,
                legendgroup=series,
                showlegend=True,
                meta={
                    "role": "entry",
                    "series": series,
                    "entry": entry_name,
                    "y_shift_px": style.get("y_shift_px") or 0,
                },
                marker={
                    "symbol": style["symbol"],
                    "size": style["size"],
                    "color": style["color"],
                    "line": {
                        "width": style.get("line_width", 1),
                        "color": style.get("line_color", style["color"]),
                    },
                },
                # Keep markers out of x-unified hover (it otherwise sticks to
                # the nearest event day). Details are on the series hover.
                hoverinfo="skip",
            )
        )


def _legend_layout(*, has_groups: bool) -> dict:
    return {
        "orientation": "h",
        "yanchor": "top",
        "y": -0.38,
        "x": 0,
        "traceorder": "grouped",
        "groupclick": "toggleitem",
        "itemclick": "toggle",
        "itemdoubleclick": "toggleothers",
        "tracegroupgap": 16 if has_groups else 10,
    }


def _show_figure(fig: go.Figure) -> None:
    import plotly.io as pio

    kwargs: dict = {"post_script": [_SERIES_LEGEND_CLICK_SCRIPT]}
    # plotly_mimetype drops post_script; force HTML so the series↔entries
    # legend hook actually runs in Jupyter / VS Code / Cursor notebooks.
    if "mimetype" in str(pio.renderers.default):
        kwargs["renderer"] = "notebook_connected"
    fig.show(**kwargs)


def final_column_values(
    outcomes: dict[str, pd.DataFrame],
    column: str = "equity",
) -> pd.Series:
    """Last ``column`` value for each experiment (by outcome key)."""
    if not outcomes:
        raise ValueError("outcomes is empty")
    values: dict[str, float] = {}
    for name, steps in outcomes.items():
        if steps.empty or column not in steps.columns:
            raise ValueError(f"outcome {name!r} has no {column!r} column")
        values[name] = float(steps[column].iloc[-1])
    return pd.Series(values)


def plot_final_equity_bars(
    outcomes: dict[str, pd.DataFrame],
    *,
    column: str = "equity",
    figsize=(10, 5),
):
    """Bar chart comparing each experiment's final ``column`` (default equity)."""
    finals = final_column_values(outcomes, column)
    colors = qualitative.Plotly
    bar_colors = [colors[i % len(colors)] for i in range(len(finals))]

    width = int(figsize[0] * 80)
    height = int(figsize[1] * 80)
    fig = go.Figure(
        go.Bar(
            x=list(finals.index),
            y=finals.values,
            marker_color=bar_colors,
            text=[f"{v:,.2f}" for v in finals.values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>" + column + ": %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        width=width,
        height=height,
        margin={"l": 60, "r": 20, "t": 40, "b": 80},
        yaxis_title=f"final {column}",
        xaxis_title=None,
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        showlegend=False,
    )
    fig.update_yaxes(tickformat=",.0f", rangemode="tozero")
    fig.update_xaxes(tickangle=-30)
    fig.show()


def plot_series(
    data,
    column,
    *,
    journal: list[EntryType] | None = None,
    scale: Scale = Scale.LOG,
    figsize=(10, 5),
):
    """Plot `column` over time with an interactive Plotly chart.

    `data` may be a single DataFrame or a dict of label -> DataFrame
    to overlay multiple series. Hover a point to see its date and value.

    Pass `journal` as a list of `EntryType` values to overlay matching
    journal entries as markers on each series. Same-day entries each keep
    their own marker (staggered in y); hover on that date lists every entry.

    Legend groups each series with its entry symbols. Toggling a series hides
    its entries too; toggling an entry symbol affects only that series.

    `scale` is ``Scale.LOG`` (default) or ``Scale.LINEAR``.
    """
    if not isinstance(scale, Scale):
        raise TypeError(f"scale must be Scale, got {type(scale)!r}")

    series = {"_": data} if isinstance(data, pd.DataFrame) else data
    width = int(figsize[0] * 80)
    height = int(figsize[1] * 80)
    colors = qualitative.Plotly
    entry_types = _entry_type_values(journal)

    fig = go.Figure()
    multi_series = len(series) > 1 or any(label != "_" for label in series)
    for index, (label, df) in enumerate(series.items()):
        frame = df.copy()
        frame["time"] = pd.to_datetime(frame["time"])
        frame[column] = frame[column].astype(float)
        series_name = column if label == "_" else label
        color = colors[index % len(colors)]

        markers: list[dict] = []
        if entry_types:
            entries = flatten_journal(frame)
            if not entries.empty:
                entries = entries[entries["type"].isin(entry_types)]
                if not entries.empty:
                    markers = aggregate_journal_markers(entries, frame, column)
                    for marker in markers:
                        marker["series"] = series_name

        fig.add_trace(
            go.Scatter(
                x=frame["time"],
                y=frame[column],
                mode="lines",
                name=column,
                legend=SERIES_LEGEND,
                legendgroup=series_name,
                legendgrouptitle_text=(
                    series_name if (multi_series or markers) else None
                ),
                meta={"role": "series", "series": series_name},
                line={"color": color},
                customdata=series_journal_customdata(frame["time"], markers),
                hovertemplate=(
                    f"<b>{series_name}</b><br>{column}: "
                    f"%{{y:{_series_y_hover_format(column)}}}%{{customdata}}"
                    f"<extra></extra>"
                ),
            )
        )
        if markers:
            _add_journal_traces(fig, markers, series=series_name)

    layout = {
        "width": width,
        "height": height,
        "hovermode": "x unified",
        "margin": {"l": 60, "r": 20, "t": 30, "b": 120},
        SERIES_LEGEND: _legend_layout(has_groups=True),
        "yaxis_title": f"{column} (log)" if scale is Scale.LOG else column,
        "xaxis_title": None,
        "plot_bgcolor": "#fafafa",
        "paper_bgcolor": "#ffffff",
    }
    fig.update_layout(**layout)
    fig.update_yaxes(type=scale.value, tickformat=",.0f")
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-45)
    _show_figure(fig)


def extract_ticker_ohlc(steps: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Rows where ``ticker`` appears in step ``candles``, as OHLC columns."""
    rows: list[dict] = []
    for _, step in steps.iterrows():
        candle = (step.get("candles") or {}).get(ticker)
        if not candle:
            continue
        rows.append(
            {
                "time": step["time"],
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["time"] = pd.to_datetime(frame["time"])
    return frame.reset_index(drop=True)


def collect_research_journal(
    outcomes: dict[str, pd.DataFrame],
    entry_types: list[str] | None = None,
) -> pd.DataFrame:
    """Flatten journals from every experiment, tagged with ``experiment``."""
    frames: list[pd.DataFrame] = []
    type_set = set(entry_types) if entry_types else None
    for name, steps in outcomes.items():
        flat = flatten_journal(steps)
        if flat.empty:
            continue
        if type_set is not None:
            flat = flat[flat["type"].isin(type_set)]
        if flat.empty:
            continue
        tagged = flat.copy()
        tagged["experiment"] = name
        frames.append(tagged)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def attach_journal_to_price(
    price: pd.DataFrame,
    journal: pd.DataFrame,
) -> pd.DataFrame:
    """Attach per-time journal lists onto a price frame (events without a bar are dropped)."""
    frame = price.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    by_time: dict = {}
    if not journal.empty:
        for _, row in journal.iterrows():
            key = pd.Timestamp(row["time"])
            by_time.setdefault(key, []).append(row.to_dict())
    frame["journal"] = [
        by_time.get(pd.Timestamp(time), []) for time in frame["time"]
    ]
    return frame


def plot_research_price(
    outcomes: dict[str, pd.DataFrame],
    ticker: str,
    *,
    bands: tuple[str, ...] = ("high", "low"),
    journal: list[EntryType] | None = None,
    scale: Scale = Scale.LOG,
    figsize=(10, 5),
):
    """One shared price chart with journal markers from every experiment.

    Price OHLC comes from steps that include ``ticker`` in ``candles``.
    Journal entries from all experiments are overlaid once (hover lists
    ``experiment: …`` for each event).
    """
    if not outcomes:
        raise ValueError("outcomes is empty")
    if not isinstance(scale, Scale):
        raise TypeError(f"scale must be Scale, got {type(scale)!r}")
    if not bands:
        raise ValueError("bands must contain at least one OHLC field")

    price = None
    for steps in outcomes.values():
        candidate = extract_ticker_ohlc(steps, ticker)
        if not candidate.empty:
            price = candidate
            break
    if price is None or price.empty:
        raise ValueError(f"No candles found for ticker {ticker!r} in outcomes")

    entry_types = _entry_type_values(journal)
    research_journal = collect_research_journal(outcomes, entry_types or None)
    frame = attach_journal_to_price(price, research_journal)

    width = int(figsize[0] * 80)
    height = int(figsize[1] * 80)
    colors = qualitative.Plotly

    markers: list[dict] = []
    if entry_types:
        entries = flatten_journal(frame)
        if not entries.empty:
            entries = entries[entries["type"].isin(entry_types)]
            if not entries.empty:
                # Place markers on the first band's y (shared market level).
                markers = aggregate_journal_markers(entries, frame, bands[0])

    fig = go.Figure()
    customdata = series_journal_customdata(frame["time"], markers)
    for index, band in enumerate(bands):
        if band not in frame.columns:
            raise ValueError(f"Unknown band {band!r}; have {list(frame.columns)}")
        name = f"{ticker} {band}"
        fig.add_trace(
            go.Scatter(
                x=frame["time"],
                y=frame[band].astype(float),
                mode="lines",
                name=name,
                legend=SERIES_LEGEND,
                legendgroup=name,
                meta={"role": "series", "series": name},
                line={"color": colors[index % len(colors)]},
                customdata=customdata if index == 0 else [""] * len(frame),
                hovertemplate=(
                    f"<b>{name}</b><br>{band}: "
                    f"%{{y:{_series_y_hover_format(band)}}}"
                    f"%{{customdata}}<extra></extra>"
                ),
            )
        )

    # One legend group per experiment; a parent legend item toggles that
    # experiment's entry markers via the series-legend click hook.
    experiments = sorted(
        {
            str(marker["series"])
            for marker in markers
            if marker.get("series")
        }
    )
    if markers and not experiments:
        experiments = ["entries"]
        for marker in markers:
            marker["series"] = "entries"

    for experiment in experiments:
        fig.add_trace(
            go.Scatter(
                x=[frame["time"].iloc[0]],
                y=[float(frame[bands[0]].iloc[0])],
                mode="markers",
                name="all",
                legend=SERIES_LEGEND,
                legendgroup=experiment,
                legendgrouptitle_text=experiment,
                meta={"role": "series", "series": experiment},
                marker={"size": 0.1, "opacity": 0, "color": "#000000"},
                hoverinfo="skip",
                showlegend=True,
            )
        )
        exp_markers = [
            marker for marker in markers if marker.get("series") == experiment
        ]
        _add_journal_traces(fig, exp_markers, series=experiment)

    layout = {
        "width": width,
        "height": height,
        "hovermode": "x unified",
        "margin": {"l": 60, "r": 20, "t": 30, "b": 140},
        SERIES_LEGEND: _legend_layout(has_groups=True),
        "yaxis_title": f"{ticker} (log)" if scale is Scale.LOG else ticker,
        "xaxis_title": None,
        "plot_bgcolor": "#fafafa",
        "paper_bgcolor": "#ffffff",
    }
    fig.update_layout(**layout)
    fig.update_yaxes(type=scale.value, tickformat=",.0f")
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-45)
    _show_figure(fig)
