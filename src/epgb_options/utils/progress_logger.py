"""
Utilidad de logging progresivo para EPGB Options.

Este módulo provee funcionalidad para actualizar logs en la misma línea
(usando carriage return) y generar resúmenes periódicos, reduciendo
el desorden en los logs durante actualizaciones frecuentes.
"""

import sys
import time
from datetime import datetime
from typing import Optional


class ProgressLogger:
    """
    Logger que permite actualizar la misma línea en lugar de crear nuevas líneas.
    
    Detecta automáticamente si la salida es a terminal (usa \\r) o a archivo (usa \\n).
    Incluye rate limiting para evitar actualizaciones excesivas.
    """
    
    def __init__(self, 
                 throttle_seconds: float = 0.5,
                 use_carriage_return: Optional[bool] = None):
        """
        Inicializar ProgressLogger.
        
        Args:
            throttle_seconds: Segundos mínimos entre actualizaciones (rate limiting)
            use_carriage_return: Si usar \\r (True), \\n (False), o auto-detectar (None)
        """
        self.throttle_seconds = throttle_seconds
        self.last_update_time = 0
        self.update_count = 0
        self.is_progress_active = False
        
        # Auto-detectar si estamos en terminal interactivo
        if use_carriage_return is None:
            self.use_carriage_return = sys.stdout.isatty()
        else:
            self.use_carriage_return = use_carriage_return
    
    def should_update(self) -> bool:
        """
        Determinar si es momento de actualizar según rate limiting.
        
        Returns:
            bool: True si debe actualizar, False si debe esperar
        """
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        
        return elapsed >= self.throttle_seconds
    
    def update(self, message: str, force: bool = False):
        """
        Actualizar el mensaje de progreso en la misma línea.
        
        Args:
            message: Mensaje a mostrar
            force: Si True, ignora rate limiting
        """
        # Rate limiting (a menos que sea forzado)
        if not force and not self.should_update():
            return
        
        self.last_update_time = time.time()
        self.update_count += 1
        self.is_progress_active = True
        
        if self.use_carriage_return:
            # Terminal interactivo: usar carriage return para sobrescribir
            # Limpiar línea actual y escribir nuevo mensaje
            sys.stdout.write(f'\r{message:<100}')  # Pad para limpiar contenido anterior
            sys.stdout.flush()
        else:
            # Archivo o redirección: usar nueva línea
            sys.stdout.write(f'{message}\n')
            sys.stdout.flush()
    
    def finish(self, final_message: Optional[str] = None):
        """
        Finalizar progreso y mover a nueva línea.
        
        Args:
            final_message: Mensaje final opcional a mostrar
        """
        if self.is_progress_active:
            if final_message:
                if self.use_carriage_return:
                    sys.stdout.write(f'\r{final_message:<100}\n')
                else:
                    sys.stdout.write(f'{final_message}\n')
            else:
                if self.use_carriage_return:
                    sys.stdout.write('\n')
            
            sys.stdout.flush()
            self.is_progress_active = False
    
    def reset(self):
        """Reiniciar contadores y estado."""
        self.last_update_time = 0
        self.update_count = 0
        self.is_progress_active = False


class ThrottledLogger:
    """
    Logger con rate limiting para evitar spam de mensajes similares.
    
    Útil para logs que se generan muy frecuentemente pero no necesitan
    ser registrados cada vez.
    """
    
    def __init__(self, base_logger, default_throttle_seconds: float = 5.0):
        """
        Inicializar ThrottledLogger.
        
        Args:
            base_logger: Logger base (de logging module)
            default_throttle_seconds: Segundos por defecto entre logs del mismo tipo
        """
        self.base_logger = base_logger
        self.default_throttle_seconds = default_throttle_seconds
        self.last_log_times = {}  # key: message_key, value: timestamp
    
    def _get_message_key(self, message: str, key: Optional[str] = None) -> str:
        """
        Obtener clave única para el mensaje (para tracking).
        
        Args:
            message: Mensaje de log
            key: Clave personalizada opcional
            
        Returns:
            str: Clave única
        """
        if key:
            return key
        
        # Usar primeras 50 caracteres del mensaje como clave
        return message[:50]
    
    def should_log(self, message: str, key: Optional[str] = None, 
                   throttle_seconds: Optional[float] = None) -> bool:
        """
        Determinar si el mensaje debe ser logueado según rate limiting.
        
        Args:
            message: Mensaje de log
            key: Clave personalizada opcional para agrupar mensajes similares
            throttle_seconds: Segundos entre logs (usa default si None)
            
        Returns:
            bool: True si debe loguear, False si debe omitir
        """
        message_key = self._get_message_key(message, key)
        current_time = time.time()
        throttle = throttle_seconds or self.default_throttle_seconds
        
        # Verificar si este mensaje fue logueado recientemente
        if message_key in self.last_log_times:
            elapsed = current_time - self.last_log_times[message_key]
            if elapsed < throttle:
                return False
        
        # Actualizar timestamp y permitir log
        self.last_log_times[message_key] = current_time
        return True
    
    def info(self, message: str, key: Optional[str] = None, 
             throttle_seconds: Optional[float] = None):
        """Log INFO con rate limiting."""
        if self.should_log(message, key, throttle_seconds):
            self.base_logger.info(message)
    
    def debug(self, message: str, key: Optional[str] = None,
              throttle_seconds: Optional[float] = None):
        """Log DEBUG con rate limiting."""
        if self.should_log(message, key, throttle_seconds):
            self.base_logger.debug(message)
    
    def warning(self, message: str, key: Optional[str] = None,
                throttle_seconds: Optional[float] = None):
        """Log WARNING con rate limiting."""
        if self.should_log(message, key, throttle_seconds):
            self.base_logger.warning(message)
    
    def error(self, message: str, key: Optional[str] = None,
              throttle_seconds: Optional[float] = None):
        """Log ERROR con rate limiting."""
        if self.should_log(message, key, throttle_seconds):
            self.base_logger.error(message)
    
    def reset(self):
        """Limpiar historial de logs (para permitir logs inmediatos)."""
        self.last_log_times.clear()


class SummaryLogger:
    """
    Genera y muestra resúmenes periódicos de estadísticas.
    
    Acumula estadísticas y las muestra cada N segundos en lugar de
    loguear cada evento individual.
    """
    
    def __init__(self, logger, interval_seconds: float = 30.0):
        """
        Inicializar SummaryLogger.
        
        Args:
            logger: Logger base para output
            interval_seconds: Segundos entre resúmenes
        """
        self.logger = logger
        self.interval_seconds = interval_seconds
        self.last_summary_time = time.time()
        self.stats = {}
        self.counters = {}
    
    def increment(self, counter_name: str, amount: int = 1):
        """
        Incrementar un contador.
        
        Args:
            counter_name: Nombre del contador
            amount: Cantidad a incrementar
        """
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += amount
    
    def set_stat(self, stat_name: str, value):
        """
        Establecer un valor de estadística.
        
        Args:
            stat_name: Nombre de la estadística
            value: Valor a establecer
        """
        self.stats[stat_name] = value
    
    def should_show_summary(self) -> bool:
        """
        Determinar si es momento de mostrar resumen.
        
        Returns:
            bool: True si debe mostrar resumen
        """
        current_time = time.time()
        elapsed = current_time - self.last_summary_time
        return elapsed >= self.interval_seconds
    
    def show_summary(self, title: str = "Resumen", force: bool = False) -> bool:
        """
        Mostrar resumen de estadísticas acumuladas.
        
        Args:
            title: Título del resumen
            force: Si True, muestra resumen sin importar intervalo
            
        Returns:
            bool: True si se mostró el resumen, False si se omitió
        """
        if not force and not self.should_show_summary():
            return False
        
        current_time = time.time()
        elapsed = current_time - self.last_summary_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Construir mensaje de resumen
        lines = [f"\n📊 {title} [{timestamp}] - ({elapsed:.1f}s desde último):"]
        
        # Agregar contadores
        if self.counters:
            for name, value in sorted(self.counters.items()):
                lines.append(f"   • {name}: {value:,}")
        
        # Agregar estadísticas
        if self.stats:
            for name, value in sorted(self.stats.items()):
                if isinstance(value, float):
                    lines.append(f"   • {name}: {value:.2f}")
                else:
                    lines.append(f"   • {name}: {value}")
        
        # Loguear resumen
        self.logger.info('\n'.join(lines))
        
        # Actualizar timestamp de último resumen
        self.last_summary_time = current_time
        
        return True
    
    def reset_counters(self):
        """Reiniciar solo contadores (mantener stats)."""
        self.counters.clear()
    
    def reset_all(self):
        """Reiniciar todo (contadores y stats)."""
        self.counters.clear()
        self.stats.clear()


def format_number(num: int) -> str:
    """
    Formatear número con separadores de miles.
    
    Args:
        num: Número a formatear
        
    Returns:
        str: Número formateado (ej: "1,234")
    """
    return f"{num:,}"


def format_duration(seconds: float) -> str:
    """
    Formatear duración en formato legible.
    
    Args:
        seconds: Segundos
        
    Returns:
        str: Duración formateada (ej: "2m 30s", "45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_rate(count: int, seconds: float) -> str:
    """
    Formatear tasa (items por segundo).
    
    Args:
        count: Cantidad de items
        seconds: Segundos transcurridos
        
    Returns:
        str: Tasa formateada (ej: "12.5/s")
    """
    if seconds <= 0:
        return "0/s"
    
    rate = count / seconds
    return f"{rate:.1f}/s"


def format_percentage(part: int, total: int) -> str:
    """
    Formatear porcentaje.
    
    Args:
        part: Parte
        total: Total
        
    Returns:
        str: Porcentaje formateado (ej: "75.5%")
    """
    if total <= 0:
        return "0%"
    
    percentage = (part / total) * 100
    return f"{percentage:.1f}%"
