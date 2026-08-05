import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# 1. Parse CSV and assign event-time timestamp
# ---------------------------------------------------------
class ParseAndTimestampDoFn(beam.DoFn):

    def process(self, element):

        # Skip CSV header
        if element.startswith("car_id"):
            return

        parts = element.split(",")

        if len(parts) != 3:
            print(f"Skipping invalid row: {element}")
            return

        car_id = parts[0].strip()
        toll_amount = float(parts[1].strip())

        # Z means UTC.
        # Convert Z to +00:00 so Python understands the timezone correctly.
        timestamp_text = parts[2].strip().replace("Z", "+00:00")

        event_time = datetime.fromisoformat(
            timestamp_text
        ).timestamp()

        yield beam.window.TimestampedValue(
            {
                "car_id": car_id,
                "toll": toll_amount,
            },
            event_time,
        )


# ---------------------------------------------------------
# 2. Convert each record to a key-value pair
# ---------------------------------------------------------
class MapToKvDoFn(beam.DoFn):

    def process(self, element):

        yield (
            "toll_revenue",
            element["toll"],
        )


# ---------------------------------------------------------
# 3. Format window result
# ---------------------------------------------------------
class FormatOutputDoFn(beam.DoFn):

    def process(
        self,
        element,
        window=beam.DoFn.WindowParam,
    ):

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

        yield (
            f"Window [{start_time} to {end_time}] "
            f"-> Total Revenue: ${total_revenue:.2f}"
        )


# ---------------------------------------------------------
# 4. Build and execute pipeline
# ---------------------------------------------------------
def run():

    # Folder containing pipeline.py
    project_directory = Path(__file__).resolve().parent

    # tolls.csv is inside the data folder
    input_file = project_directory / "data" / "tolls.csv"

    # Output will be created in the project root
    output_prefix = project_directory / "output_results"

    print("=" * 70)
    print("Apache Beam Toll Revenue Pipeline")
    print("=" * 70)
    print(f"Project folder : {project_directory}")
    print(f"Input file     : {input_file}")
    print(f"Output prefix  : {output_prefix}")
    print("=" * 70)

    # Check before Beam starts
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

            # Read CSV text
            | "ReadCSV"
            >> beam.io.ReadFromText(
                str(input_file)
            )

            # Parse and assign event timestamps
            | "ExtractEventTimestamps"
            >> beam.ParDo(
                ParseAndTimestampDoFn()
            )

            # Create fixed five-minute windows
            | "ApplyFiveMinuteWindows"
            >> beam.WindowInto(
                beam.window.FixedWindows(
                    5 * 60
                )
            )

            # Create key-value records
            | "MapToKeyValue"
            >> beam.ParDo(
                MapToKvDoFn()
            )

            # Sum toll revenue inside each window
            | "SumTollsPerWindow"
            >> beam.CombinePerKey(sum)

            # Add window boundaries to output
            | "FormatOutput"
            >> beam.ParDo(
                FormatOutputDoFn()
            )

            # Write output file
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