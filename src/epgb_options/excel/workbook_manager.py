"""
Administrador de libros de Excel para EPGB Options.

Este módulo maneja las conexiones y administración de libros de Excel.
"""

from pathlib import Path
from typing import Optional

import xlwings as xw

from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkbookManager:
    """Administra conexiones y operaciones de libros de Excel."""
    
    def __init__(self, excel_file: str, excel_path: str = "./"):
        """
        Inicializar administrador de libros.
        
        Args:
            excel_file: Nombre del archivo de Excel
            excel_path: Ruta al archivo de Excel
        """
        self.excel_file = excel_file
        self.excel_path = excel_path
        self.workbook = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Conectar al libro de Excel.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Construir ruta completa
            full_path = Path(self.excel_path) / self.excel_file
            
            # Verificar si el archivo existe
            if not full_path.exists():
                logger.error(f"Archivo de Excel no encontrado: {full_path}")
                return False
            
            # Conectar al libro
            self.workbook = xw.Book(str(full_path))
            self._is_connected = True
            
            logger.info(f"Conectado al libro de Excel: {self.excel_file}")
            return True
            
        except Exception as e:
            logger.error(f"Fallo al conectar al libro de Excel: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self):
        """Desconectar del libro de Excel."""
        if self.workbook and self._is_connected:
            try:
                # Nota: No cerramos el libro ya que podría estar en uso
                # Sólo limpiamos nuestra referencia
                self.workbook = None
                self._is_connected = False
                logger.info("Desconectado del libro de Excel")
            except Exception as e:
                logger.warning(f"Error durante la desconexión: {e}")
    
    def get_sheet(self, sheet_name: str) -> Optional[xw.Sheet]:
        """
        Obtener una hoja específica del libro.
        
        Args:
            sheet_name: Nombre de la hoja a recuperar
            
        Returns:
            xlwings.Sheet or None: Objeto Sheet si se encuentra, None en caso contrario
        """
        if not self.is_connected():
            logger.error("No conectado al libro")
            return None
        
        try:
            sheet = self.workbook.sheets(sheet_name)
            logger.debug(f"Hoja recuperada: {sheet_name}")
            return sheet
        except Exception as e:
            logger.error(f"Fallo al obtener hoja '{sheet_name}': {e}")
            return None
    
    def is_connected(self) -> bool:
        """
        Verificar si está conectado al libro.
        
        Returns:
            bool: True si está conectado, False en caso contrario
        """
        return self._is_connected and self.workbook is not None
    
    def get_workbook_info(self) -> dict:
        """
        Get information about the connected workbook.
        
        Returns:
            dict: Workbook information
        """
        if not self.is_connected():
            return {"connected": False}
        
        try:
            return {
                "connected": True,
                "file_name": self.excel_file,
                "file_path": self.excel_path,
                "sheet_names": [sheet.name for sheet in self.workbook.sheets]
            }
        except Exception as e:
            logger.error(f"Error getting workbook info: {e}")
            return {"connected": True, "error": str(e)}
    
    def save_workbook(self) -> bool:
        """
        Save the workbook.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot save - not connected to workbook")
            return False
        
        try:
            self.workbook.save()
            logger.info("Workbook saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save workbook: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()