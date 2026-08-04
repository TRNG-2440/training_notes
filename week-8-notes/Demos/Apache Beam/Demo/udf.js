function transform(line) {
  // Split the CSV line by comma
  var values = line.split(",");

  // Skip the header row
  if (values[0].trim() === "customer_id") {
    return null;
  }

  // Create an object matching the BigQuery table schema
  var obj = new Object();

  obj.customer_id = values[0].trim();
  obj.customer_name = values[1].trim();
  obj.city = values[2].trim();
  obj.state = values[3].trim();
  obj.region = values[4].trim();
  obj.segment = values[5].trim();

  // CSV date format is DD-MM-YYYY.
  // Convert it into BigQuery DATE format: YYYY-MM-DD.
  var dateParts = values[6].trim().split("-");

  if (dateParts.length === 3) {
    obj.signup_date = dateParts[2] + "-" + dateParts[1] + "-" + dateParts[0];
  } else {
    obj.signup_date = null;
  }

  obj.customer_status = values[7].trim();

  // Convert the JavaScript object into a JSON string
  var jsonString = JSON.stringify(obj);

  return jsonString;
}
