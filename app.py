def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Crear tabla si no existe
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            paquete TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL
        )
    ''')
    
    # Agregar columnas si venías de la versión anterior
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN fecha_pago TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass # La columna ya existe
        
    try:
        c.execute("ALTER TABLE clientes ADD COLUMN estado TEXT DEFAULT 'Activo'")
    except sqlite3.OperationalError:
        pass # La columna ya existe

    c.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cliente TEXT NOT NULL,
            tipo TEXT NOT NULL,
            formato TEXT NOT NULL,
            detalle TEXT
        )
    ''')
    conn.commit()
    conn.close()
