import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
import json
from typing import Any, Callable, Set
from sqlalchemy import create_engine



AZURE_PG_CONNECTION="postgresql://aiagentpostgresql.postgres.database.azure.com:5432/aiagent?user=jgordon&password=J$gg03061987&sslmode=require"


db = create_engine(AZURE_PG_CONNECTION)