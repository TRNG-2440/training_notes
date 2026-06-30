import unittest

from sales_profiler import profile_column, aggregate_sales_statistics


class TestSalesProfiler(unittest.TestCase):
    def test_profile_column_numeric(self):
        values = ["10", "20", "30", "40"]
        result = profile_column(values)

        self.assertEqual(result["type"], "numeric")
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["non_null"], 4)
        self.assertEqual(result["null_count"], 0)
        self.assertEqual(result["distinct"], 4)
        self.assertEqual(result["min"], 10.0)
        self.assertEqual(result["max"], 40.0)
        self.assertEqual(result["mean"], 25.0)

    def test_profile_column_text_and_nulls(self):
        values = ["North", "South", "", "North", "East"]
        result = profile_column(values)

        self.assertEqual(result["type"], "text")
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["non_null"], 4)
        self.assertEqual(result["null_count"], 1)
        self.assertEqual(result["distinct"], 3)
        self.assertEqual(result["null_pct"], 20.0)

    def test_profile_column_with_empty_list(self):
        values = []
        result = profile_column(values)

        self.assertEqual(result["type"], "text")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["non_null"], 0)
        self.assertEqual(result["null_count"], 0)
        self.assertEqual(result["distinct"], 0)
        self.assertEqual(result["null_pct"], 0.0)

    def test_profile_column_numeric_with_currency(self):
        values = ["$1,000.00", "$2,000.00", "$3,000.00"]
        result = profile_column(values)

        self.assertEqual(result["type"], "numeric")
        self.assertEqual(result["min"], 1000.0)
        self.assertEqual(result["max"], 3000.0)
        self.assertEqual(result["mean"], 2000.0)

    def test_aggregate_sales_statistics(self):
        rows = [
            {"quantity": "5", "unit_price": "19.99", "total_sale": "99.95"},
            {"quantity": "2", "unit_price": "49.99", "total_sale": "99.98"},
            {"quantity": "", "unit_price": "199.99", "total_sale": "199.99"},
            {"quantity": "3", "unit_price": "", "total_sale": "59.97"},
        ]

        result = aggregate_sales_statistics(rows)

        self.assertEqual(result["total_sales"], 459.89)
        self.assertEqual(result["average_quantity"], 3.33)
        self.assertEqual(result["average_unit_price"], 89.99)

    def test_aggregate_sales_statistics_missing_values(self):
        rows = [
            {"quantity": "", "unit_price": "", "total_sale": ""},
            {"quantity": "0", "unit_price": "0", "total_sale": "0"},
        ]

        result = aggregate_sales_statistics(rows)

        self.assertEqual(result["total_sales"], 0.0)
        self.assertEqual(result["average_quantity"], 0.0)
        self.assertEqual(result["average_unit_price"], 0.0)


if __name__ == "__main__":
    unittest.main()
