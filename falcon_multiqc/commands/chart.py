import click
import plotly.express as px
import pandas as pd

@click.command()
@click.option("-d", "--data", type=click.File(), required=True, help="Input CSV data to chart.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Path where output should be saved.")
@click.option("-t", "--type", type=click.Choice(["histogram", "box", "bar"], case_sensitive=False), required=True, help="Type of chart.")
@click.option("-c", "--compare", required=False, help="What column you want to compare or group by")
def cli(data, output, type, compare):
  input_df = pd.read_csv(data)

  # TODO: remove once finished development.
  print(input_df.head(5))

  metrics = []
  for col in input_df.columns:
    if col.split(".")[0] == "raw_data":
      # Column is a metric.
      metrics.append(col)

  if compare and compare not in input_df.columns:
    raise Exception(f"Selected to compare '{compare}' but {compare} is not in the input csv.")

  # Histogram supports distributions of 1 metric. Optionally comparing some column group.
  # Shows a percent (TODO: figure out if there's some way to make y-axis 'count' label say percent count).
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

  # Bar supports comparing some categorical column with 1 metric.
  elif (type == "bar"):
    fig = px.bar(input_df, x=compare, y=metrics[0])
    fig.update_xaxes(type='category')

  # Box supports comparing some column / group with 1 metric.
  elif(type == "box"):
    fig = px.box(input_df, x=compare, y=metrics[0], points="all")

  fig.write_html(output + "/graph.html")
