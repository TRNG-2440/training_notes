# Apache Beam Local Demo: Step-by-Step Student Guide

This guide walks you through setting up and running an Apache Beam pipeline locally using Python and VS Code. This demo showcases how Beam handles **PCollections**, **PTransforms**, and event-time **Windowing** using a realistic smart highway toll booth dataset.

---

## Step 1: Set Up Your Project Folder in VS Code
1. Open **VS Code** on your machine.
2. Go to the top menu and select **File** > **Open Folder...**
3. Create a new folder on your computer named `beam-demo` and select it.
4. Go to **File** > **New File**, name it `pipeline.py`, and press Enter.
5. Create another new file, name it `tolls.csv`, and press Enter.

---

## Step 2: Create the Mock Input Dataset
Open your newly created `tolls.csv` file in VS Code and paste this sample data inside it. 

*Note for students: Look closely at the timestamps. The vehicle `MNO-456` passes the toll at 12:03:00 but appears last in the file, simulating a network delay (out-of-order data).*

```csv
car_id,toll,timestamp
ABC-123,5.50,2026-08-05T12:01:00Z
XYZ-789,4.25,2026-08-05T12:06:00Z
MNO-456,6.00,2026-08-05T12:03:00Z
```

---

## Step 3: Set Up and Activate Your Virtual Environment
We will use an isolated virtual environment so we don't interfere with your computer's global Python settings.

1. Open the terminal inside VS Code by going to the top menu and selecting **Terminal** > **New Terminal**.
2. Run the command below matching your operating system to create the environment folder (`.venv`):
   * **Windows:** `python -m venv .venv`
   * **Mac / Linux:** `python3 -m venv .venv`
3. Activate the virtual environment script:
   * **Windows (Command Prompt):** `.venv\Scripts\activate.bat`
   * **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
   * **Mac / Linux:** `source .venv/bin/activate`
   
   *(Verification: You will see `(.venv)` appear at the very beginning of your terminal prompt line.)*
4. Upgrade your package installer and install Apache Beam:
   ```bash
   pip install --upgrade pip
   pip install apache-beam
   ```

---

## Step 4: Write the Apache Beam Pipeline Code
Open your `pipeline.py` file and paste the complete Python script below:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from datetime import datetime

# 1. PTransform (ParDo): Parse CSV Lines and Assign Event Timestamps
class ParseAndTimestampDoFn(beam.DoFn):
    def process(self, element):
        # Skip the CSV header row
        if element.startswith("car_id"):
            return
        
        # Split CSV line by commas
        parts = element.split(",")
        car_id = parts[0]
        toll_amount = float(parts[1])
        timestamp_str = parts[2].replace("Z", "")
        
        # Convert string to Unix Epoch timestamp
        event_time = datetime.fromisoformat(timestamp_str).timestamp()
        
        # Output a dictionary wrapped with its explicit Event Time metadata
        yield beam.window.TimestampedValue(
            {"car_id": car_id, "toll": toll_amount}, 
            event_time
        )

# 2. PTransform (ParDo): Extract Key-Value Pairs for Aggregation
class MapToKvDoFn(beam.DoFn):
    def process(self, element):
        # Key: "toll_revenue", Value: toll amount
        yield ("toll_revenue", element["toll"])

# 3. PTransform (ParDo): Format the Final Results with Window Information
class FormatOutputDoFn(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        key, total_revenue = element
        # Convert window boundaries back into human-readable text strings
        start_time = window.start.to_utc_datetime().strftime("%H:%M:%S")
        end_time = window.end.to_utc_datetime().strftime("%H:%M:%S")
        
        yield f"Window [{start_time} to {end_time}] -> Total Revenue: ${total_revenue:.2f}"

def run():
    # Use the DirectRunner to execute the pipeline locally on your computer
    options = PipelineOptions()
    
    with beam.Pipeline(runner="DirectRunner", options=options) as pipeline:
        (
            pipeline
            # PCollection 1: Read raw text lines from the local CSV file
            | "ReadCSV" >> beam.io.ReadFromText("tolls.csv")
            
            # PCollection 2: Parse text strings into structured data with timestamps
            | "ExtractTimestamps" >> beam.ParDo(ParseAndTimestampDoFn())
            
            # PCollection 3: Segment elements into Fixed 5-Minute Window intervals
            | "ApplyFixedWindows" >> beam.WindowInto(beam.window.FixedWindows(5 * 60))
            
            # PCollection 4: Convert elements to Key-Value pairs
            | "MapToKV" >> beam.ParDo(MapToKvDoFn())
            
            # PCollection 5: Aggregate totals. Beam scopes this sum per Window block!
            | "SumTollsPerWindow" >> beam.CombinePerKey(sum)
            
            # PCollection 6: Inject window start/end times into our text output
            | "FormatOutput" >> beam.ParDo(FormatOutputDoFn())
            
            # Sink: Write results to local text files
            | "WriteToLocalFile" >> beam.io.WriteToText("output_results")
        )

if __name__ == "__main__":
    run()
    print("\n Pipeline execution complete! Check your folder for 'output_results-00000-of-00001'.\n")
```

---

## Step 5: Execute the Pipeline Manually
1. Make sure your virtual environment is still active in your terminal (`(.venv)` should be visible).
2. Start the local pipeline runtime execution by typing this command into your terminal:
   ```bash
   python pipeline.py
   ```
3. Once finished, a confirmation message will print to the screen.

---

## Step 6: Reviewing the Concepts with Students
Look at your VS Code File Explorer panel on the left side. Open the newly generated file named `output_results-00000-of-00001` to view the outputs:

```text
Window [12:00:00 to 12:05:00] -> Total Revenue: \$11.50
Window [12:05:00 to 12:10:00] -> Total Revenue: \$4.25
```

### Core Teaching Moments to Explain:
1. **PCollection & PTransform:** Every step (demarcated by `|`) converts an immutable data pool (`PCollection`) into a new structured pool using an operation (`PTransform`).
2. **Event-Time vs. Processing-Time:** Even though `MNO-456` (12:03:00) was ordered *last* in our text file, Apache Beam read its internal timestamp metadata and correctly grouped its `$6.00` fee into the **12:00 to 12:05** window alongside `ABC-123` ($5.50 + $6.00 = $11.50). 
3. **Window Isolation:** `XYZ-789` (12:06:00) fell outside the first 5-minute block boundaries and was seamlessly isolated into its own independent **12:05 to 12:10** bucket allocation.
