# PySpark Data Loading, Saving and Pair RDD Retail Demo

## Execution choices

- VS Code local PySpark: RDD supported.
- Databricks classic/Dedicated: RDD supported.
- Current Databricks Free Edition: RDD unsupported; use the included DataFrame alternative.

## VS Code setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python src\01_rdd_loading_methods.py
python src\02_simple_pair_rdd.py
python src\03_retail_pair_rdd_pipeline.py
python src\04_rdd_saving_methods.py
```

## Verified results

- Input: 20
- Valid: 18
- Rejected: 2
- Completed report orders: 15
- Electronics revenue: 204540
- Fashion revenue: 25420
- Grocery revenue: 9074

## Databricks

- `databricks/Retail_Data_Loading_Pair_RDD_Legacy_Classic.dbc`
- `databricks/Retail_Data_Loading_Free_Edition_DataFrame_Alternative.dbc`
