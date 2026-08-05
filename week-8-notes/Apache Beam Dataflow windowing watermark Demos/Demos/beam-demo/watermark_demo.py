import apache_beam as beam

from apache_beam.options.pipeline_options import (
    PipelineOptions,
    StandardOptions,
)
from apache_beam.testing.test_stream import TestStream
from apache_beam.transforms.trigger import (
    AccumulationMode,
    AfterCount,
    AfterWatermark,
)
from apache_beam.utils.timestamp import Timestamp


# ---------------------------------------------------------
# Convert a toll dictionary into a Beam key-value tuple
# ---------------------------------------------------------
def map_to_key_value(element):
    """
    Input:
        {
            "car_id": "CAR-001",
            "toll": 5.50
        }

    Output:
        ("toll_revenue", 5.50)
    """

    return (
        "toll_revenue",
        element["toll"],
    )


# ---------------------------------------------------------
# Format every pane emitted by the trigger
# ---------------------------------------------------------
def format_result(
    element,
    window=beam.DoFn.WindowParam,
    pane_info=beam.DoFn.PaneInfoParam,
):
    """
    element:
        ("toll_revenue", total)

    window:
        Beam IntervalWindow

    pane_info:
        Information about the pane that Beam emitted.
    """

    key, total_revenue = element

    window_start = (
        window.start
        .to_utc_datetime()
        .strftime("%H:%M:%S")
    )

    window_end = (
        window.end
        .to_utc_datetime()
        .strftime("%H:%M:%S")
    )

    return (
        f"Window [{window_start} to {window_end}] | "
        f"Pane timing: {pane_info.timing} | "
        f"Pane index: {pane_info.index} | "
        f"Revenue: ${total_revenue:.2f}"
    )


# ---------------------------------------------------------
# Print output produced by each pane
# ---------------------------------------------------------
def print_result(element):
    print(element)
    return element


# ---------------------------------------------------------
# Create the watermark demonstration pipeline
# ---------------------------------------------------------
def run():
    options = PipelineOptions()

    # TestStream represents an unbounded stream.
    options.view_as(StandardOptions).streaming = True

    # -----------------------------------------------------
    # Window:
    # [12:00, 12:05)
    #
    # CAR-001 and CAR-002 arrive before the watermark
    # reaches 12:05.
    #
    # The watermark then reaches the end of the window,
    # causing the on-time pane.
    #
    # CAR-003 arrives afterward, but its event timestamp
    # is 12:03. It therefore belongs to the old window
    # and is treated as late data.
    # -----------------------------------------------------

    test_stream = (
        TestStream()

        # Begin the simulated event-time clock.
        .advance_watermark_to(
            Timestamp.from_rfc3339(
                "2026-08-05T12:00:00Z"
            )
        )

        # Event 1 belongs to [12:00, 12:05).
        .add_elements(
            [
                beam.window.TimestampedValue(
                    {
                        "car_id": "CAR-001",
                        "toll": 5.50,
                    },
                    Timestamp.from_rfc3339(
                        "2026-08-05T12:01:00Z"
                    ),
                )
            ]
        )

        # Event 2 also belongs to [12:00, 12:05).
        .add_elements(
            [
                beam.window.TimestampedValue(
                    {
                        "car_id": "CAR-002",
                        "toll": 7.25,
                    },
                    Timestamp.from_rfc3339(
                        "2026-08-05T12:02:00Z"
                    ),
                )
            ]
        )

        # Move the watermark to the end of the window.
        # Beam can now emit the on-time pane.
        .advance_watermark_to(
            Timestamp.from_rfc3339(
                "2026-08-05T12:05:00Z"
            )
        )

        # This record arrives after the watermark has
        # reached 12:05.
        #
        # Its event timestamp is 12:03, so it belongs to
        # the earlier [12:00, 12:05) window.
        .add_elements(
            [
                beam.window.TimestampedValue(
                    {
                        "car_id": "CAR-003",
                        "toll": 4.75,
                    },
                    Timestamp.from_rfc3339(
                        "2026-08-05T12:03:00Z"
                    ),
                )
            ]
        )

        # Complete the simulated stream.
        .advance_watermark_to_infinity()
    )

    with beam.Pipeline(
        runner="DirectRunner",
        options=options,
    ) as pipeline:

        (
            pipeline

            # Source: simulated unbounded stream
            | "CreateTestStream"
            >> test_stream

            # Group events into five-minute event-time windows
            | "ApplyFiveMinuteWindows"
            >> beam.WindowInto(
                beam.window.FixedWindows(
                    5 * 60
                ),

                # Emit the normal result when the watermark
                # reaches the end of the window.
                #
                # Emit another pane whenever one late record
                # arrives.
                trigger=AfterWatermark(
                    late=AfterCount(1)
                ),

                # Retain the window for two additional minutes
                # of event-time watermark progression.
                allowed_lateness=2 * 60,

                # Each later pane contains the previous values
                # plus newly arrived values.
                accumulation_mode=(
                    AccumulationMode.ACCUMULATING
                ),
            )

            # Convert each record into:
            # ("toll_revenue", toll_amount)
            | "MapToKeyValue"
            >> beam.Map(
                map_to_key_value
            )

            # Calculate the total for each window
            | "SumRevenuePerWindow"
            >> beam.CombinePerKey(sum)

            # Include window and pane information
            | "FormatResults"
            >> beam.Map(
                format_result
            )

            # Print each pane
            | "PrintResults"
            >> beam.Map(
                print_result
            )
        )


if __name__ == "__main__":
    run()

