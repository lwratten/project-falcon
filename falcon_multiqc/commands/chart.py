import sys
import click
import math
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

SUBPLOT_ROWS = 2
SUBPLOT_COLS = 2

def subplot(metrics):
  return make_subplots(
    rows=(math.ceil(len(metrics) / SUBPLOT_ROWS)),
    cols=SUBPLOT_COLS,
    start_cell="top-left",
    subplot_titles=metrics)

def getRow(i):
  return (i//SUBPLOT_ROWS) + 1

def getCol(i):
  return ((i%SUBPLOT_COLS) + 1)

@click.command()
@click.option("-d", "--data", type=click.File(), help="Input CSV data to chart.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Path where output should be saved (including file name).")
@click.option("-t", "--type", type=click.Choice(["histogram", "box", "bar"], case_sensitive=False), required=True, help="Type of chart.")
@click.option("-c", "--compare", required=False, help="What column you want to compare or group by")
def cli(data, output, type, compare):
  """Chart data from the query command. Requires csv input (--data or stdin)."""
  if data:
    input_df = pd.read_csv(data)
  elif sys.stdin.isatty(): # Stdin
    data = click.get_text_stream('stdin').value()
  else:
    raise Exception("Chart requires csv data input via --data or stdin.")  

  click.echo("First 5 lines of your input...")
  click.echo(input_df.head(5))

  metrics = []
  for col in input_df.columns:
    if col.split(".")[0] == "raw_data":
      # Column is a metric.
      metrics.append(col)

  if compare and compare not in input_df.columns:
    raise Exception(f"Selected to compare '{compare}' but {compare} is not in the input csv.")

  # Histogram supports distributions of 1 metric. Optionally comparing some column group.
  # Shows count Y axis as a percentage.
  if (type == "histogram"):
    fig = px.histogram(
      input_df,
      x=metrics[0],
      title=metrics[0],
      marginal="rug", # Shows a separate distribution graph up top.
      color=compare,
      barmode="overlay",
      histnorm="percent",
      hover_data=input_df.columns)

    fig.layout.yaxis.title.text = 'Count (Percent)'

  # Bar supports comparing some categorical column with multiple metrics.
  # Requires 'compare'.
  elif (type == "bar"):
    if (not compare):
      raise Exception("Bar chart requires --compare field to plot the x axis.")
    if (len(metrics) == 1):
      fig = px.bar(input_df, x=compare, y=metrics[0])
    else:
      fig = subplot(metrics)

      # Plot every (raw_data) metric in the given input.
      for i in range(len(metrics)):
        row = getRow(i)
        col = getCol(i)
        fig.add_trace(go.Bar(x=input_df[compare], y=input_df[metrics[i]]),
                      row=row, col=col)
        fig.update_xaxes(title_text=compare, row=row, col=col)
        fig.update_yaxes(title_text=metrics[i], row=row, col=col)
        # Note: duplicate 'compare' x values are overlayed, and therefore may be hidden.
        fig.update_layout(barmode="overlay", showlegend=False)

    fig.update_xaxes(type='category')

  # Box supports comparing some column / group with multiple metric.
  elif(type == "box"):
    if (len(metrics) == 1):
      fig = px.box(input_df, x=compare, y=metrics[0], points="all")
    else:
      fig = subplot(metrics)

      for i in range(len(metrics)):
        row = getRow(i)
        col = getCol(i)
        fig.add_trace(go.Box(x=(input_df[compare] if compare else None), y=input_df[metrics[i]]),
                      row=row, col=col)
        if (compare):
          fig.update_xaxes(title_text=compare, row=row, col=col)

        fig.update_yaxes(title_text=metrics[i], row=row, col=col)

      fig.update_layout(showlegend=False)

  fig.write_html(output)
