import logging
from langfuse import observe
from app.core.constants import COLUMN_MAPPING

logger = logging.getLogger(__name__)

@observe(as_type="span")
def calculate_metrics(query_type: str, numerator_data: list, denominator_data: list = None):
    results = []
    
    if not numerator_data:
        return results
        
    for row in numerator_data:
        clean_row = {}
        
        # Map database columns to display labels
        for database_column, display_label in COLUMN_MAPPING.items():
            if database_column in row:
                clean_row[display_label] = row[database_column]
        
        try:
            if query_type == "price":
                val = row.get("Fact__valuesSum", 0)
                vol = row.get("Fact__volumeSum", 1) # Prevent division by zero
                metric_val = val / vol if vol else 0
                metric_label = "Price (SAR)"
                
            elif query_type == "growth":
                cy = row.get("Fact__valuesSum", 0)
                ly = row.get("Fact__valuesLYSum", 1)
                metric_val = ((cy - ly) / ly) * 100 if ly else 0
                metric_label = "Growth (%)"
                
            elif query_type == "share":
                brand_val = row.get("Fact__valuesSum", 0)
                total_val = denominator_data[0].get("Fact__valuesSum", 1)
   
                metric_val = (brand_val / total_val) * 100 if total_val else 0
                metric_label = "Share (%)"
                
            elif query_type == "sales":
                metric_val = row.get("Fact__valuesSum", 0)
                metric_label = "Sales"
                
            else:
                metric_val = row.get("Fact__valuesSum", 0)
                metric_label = "Value"
                
            # Save ONLY the final formatted result to the clean row
            clean_row[metric_label] = f"{metric_val:,.2f}"
            
        except Exception as e:
            logger.error(f"Calculation error for row {row}: {e}")
            clean_row["Error"] = "Failed to calculate"
            
        results.append(clean_row)
        
    return results
