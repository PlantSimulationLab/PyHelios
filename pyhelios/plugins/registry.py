"""
Plugin registry for centralized plugin management in PyHelios.

This module provides a central registry for managing plugin availability,
capabilities, and runtime state across the PyHelios system.
"""

import logging
from typing import Dict, List, Optional, Set, Any, Callable
from functools import wraps

from .loader import (
    get_loader, 
    detect_available_plugins, 
    is_plugin_available, 
    get_plugin_capabilities,
    LibraryLoadError
)

try:
    from ..config.plugin_metadata import PLUGIN_METADATA, get_all_plugin_names
except ImportError:
    PLUGIN_METADATA = {}
    get_all_plugin_names = lambda: []

logger = logging.getLogger(__name__)


class PluginNotAvailableError(Exception):
    """Raised when attempting to use an unavailable plugin."""
    pass


class PluginRegistry:
    """Central registry for runtime plugin detection and management."""
    
    def __init__(self):
        """Initialize the plugin registry."""
        self._available_plugins: Optional[Set[str]] = None
        self._plugin_capabilities: Optional[Dict[str, Dict[str, Any]]] = None
        self._failed_plugins: Set[str] = set()
        self._initialized = False
        
        logger.info("Initialized PyHelios plugin registry")
    
    def initialize(self, force_refresh: bool = False) -> None:
        """
        Initialize the plugin registry by scanning available plugins.
        
        Args:
            force_refresh: Force re-scanning even if already initialized
        """
        if self._initialized and not force_refresh:
            return
        
        try:
            logger.info("Scanning for available plugins...")
            
            # Detect available plugins
            available_list = detect_available_plugins()
            self._available_plugins = set(available_list)
            
            # Get plugin capabilities
            self._plugin_capabilities = get_plugin_capabilities()
            
            # Clear failed plugins on successful initialization
            self._failed_plugins.clear()
            
            self._initialized = True
            
            logger.info(f"Plugin registry initialized with {len(self._available_plugins)} plugins: {sorted(self._available_plugins)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin registry: {e}")
            # Initialize with empty sets so the system can still function
            self._available_plugins = set()
            self._plugin_capabilities = {}
            self._initialized = True
    
    def get_available_plugins(self) -> List[str]:
        """
        Get list of available plugins.
        
        Returns:
            List of available plugin names
        """
        if not self._initialized:
            self.initialize()
        
        return sorted(list(self._available_plugins or []))
    
    def is_plugin_available(self, plugin_name: str) -> bool:
        """
        Check if a specific plugin is available.
        
        Args:
            plugin_name: Name of the plugin to check
            
        Returns:
            True if plugin is available, False otherwise
        """
        if not self._initialized:
            self.initialize()
        
        return plugin_name in (self._available_plugins or set())
    
    def get_plugin_capabilities(self, plugin_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get plugin capabilities information.
        
        Args:
            plugin_name: Specific plugin name, or None for all plugins
            
        Returns:
            Plugin capabilities dictionary
        """
        if not self._initialized:
            self.initialize()
        
        if plugin_name is None:
            return self._plugin_capabilities or {}
        
        capabilities = self._plugin_capabilities or {}
        return capabilities.get(plugin_name, {})
    
    def require_plugin(self, plugin_name: str, feature_description: str = None) -> None:
        """
        Require that a plugin is available, raising an error if not.
        
        Args:
            plugin_name: Name of the required plugin
            feature_description: Description of the feature requiring the plugin
            
        Raises:
            PluginNotAvailableError: If plugin is not available
        """
        if not self.is_plugin_available(plugin_name):
            feature_text = f" for {feature_description}" if feature_description else ""
            
            # Provide helpful error message with plugin information
            error_msg = f"Plugin '{plugin_name}' is required{feature_text} but is not available."
            
            if plugin_name in PLUGIN_METADATA:
                metadata = PLUGIN_METADATA[plugin_name]
                error_msg += f"\n\nPlugin Info:"
                error_msg += f"\n- Description: {metadata.description}"
                if metadata.gpu_required:
                    error_msg += f"\n- Requires GPU support"
                if metadata.system_dependencies:
                    error_msg += f"\n- System dependencies: {', '.join(metadata.system_dependencies)}"
            
            error_msg += f"\n\nTo enable this plugin:"
            error_msg += f"\n1. Build PyHelios with the plugin: build_scripts/build_helios --plugins {plugin_name}"
            error_msg += f"\n2. Or build with multiple plugins: build_scripts/build_helios --plugins {plugin_name},visualizer,weberpenntree"
            
            # Mark as failed for future reference
            self._failed_plugins.add(plugin_name)
            
            raise PluginNotAvailableError(error_msg)
    
    def get_missing_plugins(self, requested_plugins: List[str]) -> List[str]:
        """
        Get list of requested plugins that are not available.
        
        Args:
            requested_plugins: List of plugin names to check
            
        Returns:
            List of missing plugin names
        """
        if not self._initialized:
            self.initialize()
        
        available = self._available_plugins or set()
        return [p for p in requested_plugins if p not in available]
    
    def suggest_alternatives(self, failed_plugin: str) -> List[str]:
        """
        Suggest alternative plugins when one is not available.
        
        Args:
            failed_plugin: Name of the plugin that failed
            
        Returns:
            List of suggested alternative plugin names
        """
        if not self._initialized:
            self.initialize()
        
        # Plugin alternative suggestions
        alternatives = {
            'radiation': ['energybalance', 'leafoptics'],
            'visualizer': ['syntheticannotation'],
            'aeriallidar': ['lidar'],
            'collisiondetection': ['voxelintersection'],
            'projectbuilder': [],
        }
        
        suggested = alternatives.get(failed_plugin, [])
        available = self._available_plugins or set()
        
        # Only suggest alternatives that are actually available
        return [alt for alt in suggested if alt in available]
    
    def get_failed_plugins(self) -> List[str]:
        """Get list of plugins that have failed to load or been marked as failed."""
        return sorted(list(self._failed_plugins))
    
    def get_plugin_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of plugin status.
        
        Returns:
            Dictionary with plugin status summary
        """
        if not self._initialized:
            self.initialize()
        
        all_plugins = get_all_plugin_names()
        available = self._available_plugins or set()
        
        return {
            'total_plugins': len(all_plugins),
            'available_plugins': len(available),
            'missing_plugins': len(all_plugins) - len(available),
            'failed_plugins': len(self._failed_plugins),
            'available_list': sorted(list(available)),
            'missing_list': sorted([p for p in all_plugins if p not in available]),
            'failed_list': sorted(list(self._failed_plugins)),
            'gpu_plugins_available': len([p for p in available if PLUGIN_METADATA.get(p) and getattr(PLUGIN_METADATA[p], 'gpu_required', False)]),
            'capabilities': self._plugin_capabilities or {}
        }
    
    def print_status(self):
        """Print detailed plugin status information."""
        summary = self.get_plugin_summary()
        
        print("PyHelios Plugin Registry Status")
        print("=" * 32)
        print(f"Total Plugins: {summary['total_plugins']}")
        print(f"Available: {summary['available_plugins']}")
        print(f"Missing: {summary['missing_plugins']}")
        print(f"Failed: {summary['failed_plugins']}")
        print(f"GPU Plugins Available: {summary['gpu_plugins_available']}")
        
        if summary['available_list']:
            print(f"\nAvailable Plugins ({summary['available_plugins']}):")
            for plugin in summary['available_list']:
                capabilities = summary['capabilities'].get(plugin, {})
                # Check both capabilities (from detection) and metadata (from plugin definitions)
                gpu_required = (capabilities.get('gpu_required', False) or 
                               (PLUGIN_METADATA.get(plugin) and getattr(PLUGIN_METADATA[plugin], 'gpu_required', False)))
                gpu_indicator = " (GPU)" if gpu_required else ""
                print(f"  ✓ {plugin}{gpu_indicator}")
        
        if summary['missing_list']:
            print(f"\nMissing Plugins ({summary['missing_plugins']}):")
            for plugin in summary['missing_list']:
                print(f"  ✗ {plugin}")
        
        if summary['failed_list']:
            print(f"\nFailed Plugins ({summary['failed_plugins']}):")
            for plugin in summary['failed_list']:
                print(f"  ⚠ {plugin}")


def require_plugin(plugin_name: str, feature_description: str = None):
    """
    Decorator to require a plugin for a function or method.
    
    Args:
        plugin_name: Name of the required plugin
        feature_description: Description of the feature requiring the plugin
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            registry = get_plugin_registry()
            registry.require_plugin(plugin_name, feature_description or func.__name__)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def graceful_plugin_fallback(plugin_name: str, fallback_result: Any = None, 
                           warning_message: str = None):
    """
    Decorator to provide graceful fallback when a plugin is not available.
    
    Args:
        plugin_name: Name of the required plugin
        fallback_result: Result to return if plugin is not available
        warning_message: Custom warning message to display
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            registry = get_plugin_registry()
            
            if not registry.is_plugin_available(plugin_name):
                message = warning_message or f"Plugin '{plugin_name}' not available for {func.__name__}"
                logger.warning(message)
                
                # Suggest alternatives if available
                alternatives = registry.suggest_alternatives(plugin_name)
                if alternatives:
                    logger.info(f"Available alternatives: {alternatives}")
                
                return fallback_result
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global plugin registry instance
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _plugin_registry
    
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
        _plugin_registry.initialize()
    
    return _plugin_registry


def reset_plugin_registry():
    """Reset the global plugin registry (useful for testing)."""
    global _plugin_registry
    _plugin_registry = None