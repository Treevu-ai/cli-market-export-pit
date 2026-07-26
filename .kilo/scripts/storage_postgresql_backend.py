# Key changes to src/pitchavi/storage.py for PostgreSQL support:
# 1. Added psycopg2 import with fallback
# 2. __init__ accepts database_url param
# 3. _connect returns psycopg2 or sqlite3 connection
# 4. _transaction doesn't close PostgreSQL connections
# 5. _execute replaces ? with %s for PostgreSQL
# 6. initialize() uses per-statement execution for PostgreSQL
