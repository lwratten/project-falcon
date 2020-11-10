import click
import plotly.express as px
import pandas as pd

columns = {
  "cohort" : "cohort.id",
  "sample" : "sample.id",
  "batch" : "batch.batch_name",
}

@click.command()
@click.option("-d", "--data", type=click.File(), required=True, help="Input CSV data to chart.")
@click.option("-o", "--output", type=click.Path(), required=True, help="Path where output should be saved.")
@click.option("-t", "--type", type=click.Choice(["histogram", "line"], case_sensitive=False), required=True, help="Type of chart.")
@click.option("-c", "--compare", type=click.Choice(["sample", "batch", "cohort", "metric"], case_sensitive=False), required=True, help="What column do you want to compare on the chart?")
def cli(data, output, type, compare):
  input_df = pd.read_csv(data)

  # TODO: remove once finished development.
  print(input_df.head(5))

  metrics = []
  for col in input_df.columns:
    if col.split(".")[0] == "raw_data":
      # Column is a metric.
      metrics.append(col)

  # TODO: support every column output of query.
  if compare == "cohort" and columns["cohort"] not in input_df.columns:
    raise Exception("Selected to compare 'cohort' but cohort.id is not in the input csv.")

  elif compare == "sample" and columns["sample"] not in input_df.columns:
    raise Exception("Selected to compare 'sample' but sample.id is not in the input csv.")

  elif compare == "batch" and "batch.batch_name" not in input_df.columns:
    raise Exception("Selected to compare 'batch' but batch.batch_name is not in the input csv.")

  elif compare == "metric" and len(metrics) == 0:
    raise Exception("Selected to compare 'metric' but no raw_data columns found in input csv.")

  if (type == "histogram"):
    # TODO: support more than 1 metric.
    
    fig = px.histogram(
      input_df,
      x=metrics[0],
      title=metrics[0],
      marginal="rug", # Shows a separate distribution graph up top.
      color=columns[compare],
      barmode="overlay",
      histnorm="percent",
      hover_data=input_df.columns)    

    fig.write_html(output + "/graph.html")
