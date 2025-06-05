import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseUtils:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information including column names and types"""
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.engine)
            
            columns = []
            for column in table.columns:
                columns.append({
                    "name": column.name,
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key
                })
            
            return {
                "table_name": table_name,
                "columns": columns,
                "column_count": len(columns)
            }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            raise
    
    def get_record_count(self, table_name: str, date_column: str, target_date: str) -> int:
        """Get record count for a specific date"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {date_column} = :target_date"
            result = self.execute_query(query, {"target_date": target_date})
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting record count: {e}")
            return 0
    
    def get_date_range_data(self, table_name: str, date_column: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get data for a date range as DataFrame"""
        try:
            query = f"""
            SELECT {date_column}, COUNT(*) as record_count
            FROM {table_name}
            WHERE {date_column} BETWEEN :start_date AND :end_date
            GROUP BY {date_column}
            ORDER BY {date_column}
            """
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
            
            return df
        except Exception as e:
            logger.error(f"Error getting date range data: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()