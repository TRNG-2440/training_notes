/**
 * Dataflow "Text Files on Cloud Storage to BigQuery" JavaScript UDF.
 * Converts one CSV line into a JSON string matching the BigQuery schema.
 *
 * Important:
 * - The Dataflow template invokes the function once per text line.
 * - This basic parser is suitable for the supplied sample, which has no
 *   embedded commas inside quoted values.
 */
function transform(line) {
  var values = line.split(",");

  // Ignore the CSV header. Returning null drops the line.
  if (values[0] === "order_id") {
    return null;
  }

  if (values.length !== 7) {
    throw new Error("Expected 7 columns but found " + values.length + ": " + line);
  }

  var record = {
    order_id: parseInt(values[0], 10),
    customer_name: values[1].trim(),
    city: values[2].trim(),
    state: values[3].trim(),
    category: values[4].trim(),
    amount: parseFloat(values[5]),
    order_date: values[6].trim()
  };

  return JSON.stringify(record);
}
