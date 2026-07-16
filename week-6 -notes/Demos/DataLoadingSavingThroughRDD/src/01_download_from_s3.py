S3_URL = (
    "https://noaa-gsod-pds.s3.amazonaws.com/"
    "2024/01001099999.csv"
)

urllib.request.urlretrieve(
    S3_URL,
    DOWNLOADED_FILE,
)

raw_lines = sc.textFile(
    DOWNLOADED_FILE.resolve().as_uri(),
    4,
)

header = raw_lines.first()

data_lines = raw_lines.filter(
    lambda line: line != header
)