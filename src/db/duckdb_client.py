import duckdb
import os
from typing import List, Any
from schemas.crypto import PrecioActivo, IndicadorTecnico
from schemas.sports import CuotaDeportiva, AnalisisPartido
from schemas.news import EventoNoticia

class DuckDBClient:
    def __init__(self, db_path: str = "market_data.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        # Crear tabla para PrecioActivo
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS precio_activo (
                simbolo VARCHAR,
                precio DOUBLE,
                volumen_24h DOUBLE,
                timestamp TIMESTAMP,
                fuente VARCHAR
            )
        """)

        # Crear tabla para IndicadorTecnico
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS indicador_tecnico (
                simbolo VARCHAR,
                rsi DOUBLE,
                macd DOUBLE,
                dominancia DOUBLE,
                timestamp TIMESTAMP
            )
        """)

        # Crear tabla para CuotaDeportiva
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cuota_deportiva (
                evento VARCHAR,
                equipo_local VARCHAR,
                equipo_visitante VARCHAR,
                cuota_local DOUBLE,
                cuota_empate DOUBLE,
                cuota_visitante DOUBLE,
                fuente VARCHAR,
                timestamp TIMESTAMP
            )
        """)

        # Crear tabla para EventoNoticia
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evento_noticia (
                titulo VARCHAR,
                resumen VARCHAR,
                fuente VARCHAR,
                url VARCHAR,
                impacto_estimado VARCHAR,
                categoria VARCHAR,
                timestamp TIMESTAMP
            )
        """)

    def insert_precios(self, precios: List[PrecioActivo]):
        if not precios:
            return
        # Usamos una lista de tuplas para inserción masiva (bulk insert)
        data = [
            (p.simbolo, p.precio, p.volumen_24h, p.timestamp, p.fuente) 
            for p in precios
        ]
        self.conn.executemany("""
            INSERT INTO precio_activo VALUES (?, ?, ?, ?, ?)
        """, data)

    def insert_noticias(self, noticias: List[EventoNoticia]):
        if not noticias:
            return
        data = [
            (n.titulo, n.resumen, n.fuente, n.url, n.impacto_estimado, n.categoria, n.timestamp)
            for n in noticias
        ]
        self.conn.executemany("""
            INSERT INTO evento_noticia VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)

    def insert_cuotas(self, cuotas: List[CuotaDeportiva]):
        if not cuotas:
            return
        data = [
            (c.evento, c.equipo_local, c.equipo_visitante, c.cuota_local, c.cuota_empate, c.cuota_visitante, c.fuente, c.timestamp)
            for c in cuotas
        ]
        self.conn.executemany("""
            INSERT INTO cuota_deportiva VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

    def close(self):
        self.conn.close()
