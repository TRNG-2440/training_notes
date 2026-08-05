import apache_beam as beam

from apache_beam.options.pipeline_options import PipelineOptions
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# 1. Parse one CSV line
# ---------------------------------------------------------
def parse_and_add_timestamp(element):
    """
    Parse one CSV row and assign its event timestamp.

    FlatMap is used because:
    - Header produces zero output records.
    - Valid data row produces one output record.
    """

    # Skip header
    if element.startswith("car_id"):
        return []

    parts = element.split(",")

    # Skip malformed rows
    if len(parts) != 3:
        print(f"Skipping malformed row: {element}")
        return []

    try:
        car_id = parts[0].strip()
        toll_amount = float(parts[1].strip())

        # Convert UTC Z notation into Python-compatible timezone notation
        timestamp_text = (
            parts[2]
            .strip()
            .replace("Z", "+00:00")
        )

        event_timestamp = datetime.fromisoformat(
            timestamp_text
        ).timestamp()

        record = {
            "car_id": car_id,
            "toll": toll_amount,
        }

        return [
            beam.window.TimestampedValue(
                record,
                event_timestamp,
            )
        ]

    except (ValueError, IndexError) as error:
        print(
            f"Skipping invalid row: {element}. "
            f"Reason: {error}"
        )
        return []


# ---------------------------------------------------------
# 2. Convert record into key-value format
# ---------------------------------------------------------
def map_to_key_value(element):
    """
    One input produces exactly one output.

    Input:
        {"car_id": "CAR-001", "toll": 5.50}

    Output:
        ("toll_revenue", 5.50)
    """

    return (
        "toll_revenue",
        element["toll"],
    )


# ---------------------------------------------------------
# 3. Format final window result
# ---------------------------------------------------------
def format_output(
    element,
    window=beam.DoFn.WindowParam,
):
    """
    Format the aggregated result and include window boundaries.
    """

    key, total_revenue = element

    start_time = (
        window.start
        .to_utc_datetime()
        .strftime("%H:%M:%S")
    )

    end_time = (
        window.end
        .to_utc_datetime()
        .strftime("%H:%M:%S")
    )

    return (
        f"Window [{start_time} to {end_time}] "
        f"-> Total Revenue: ${total_revenue:.2f}"
    )


# ---------------------------------------------------------
# 4. Create and run pipeline
# ---------------------------------------------------------
def run():

    project_directory = Path(__file__).resolve().parent

    input_file = (
        project_directory
        / "data"
        / "tolls.csv"
    )

    output_prefix = (
        project_directory
        / "output_results"
    )

    print("=" * 70)
    print("Apache Beam Toll Revenue Pipeline")
    print("=" * 70)
    print(f"Input file    : {input_file}")
    print(f"Output prefix : {output_prefix}")
    print("=" * 70)

    if not input_file.exists():
        raise FileNotFoundError(
            "\nInput CSV file was not found.\n"
            f"Expected location:\n{input_file}\n"
        )

    options = PipelineOptions()

    with beam.Pipeline(
        runner="DirectRunner",
        options=options,
    ) as pipeline:

        (
            pipeline

            # PCollection[str]
            | "ReadCSV"
            >> beam.io.ReadFromText(
                str(input_file)
            )

            # PCollection[TimestampedValue]
            | "ParseAndTimestamp"
            >> beam.FlatMap(
                parse_and_add_timestamp
            )

            # Place records into five-minute event-time windows
            | "ApplyFiveMinuteWindows"
            >> beam.WindowInto(
                beam.window.FixedWindows(
                    5 * 60
                )
            )

            # PCollection[tuple[str, float]]
            | "MapToKeyValue"
            >> beam.Map(
                map_to_key_value
            )

            # Sum toll values separately inside each window
            | "SumRevenuePerWindow"
            >> beam.CombinePerKey(sum)

            # PCollection[str]
            | "FormatResult"
            >> beam.Map(
                format_output
            )

            # Local text output
            | "WriteOutput"
            >> beam.io.WriteToText(
                str(output_prefix)
            )
        )


if __name__ == "__main__":
    run()

    print()
    print("Pipeline execution completed successfully.")
    print(
        "Check the project folder for "
        "'output_results-00000-of-00001'."
    )