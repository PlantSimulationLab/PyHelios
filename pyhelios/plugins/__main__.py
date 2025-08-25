"""
Plugin status and discovery command-line interface for PyHelios.

This module provides command-line tools for checking plugin availability,
system compatibility, and generating configuration recommendations.

Usage:
    python -m pyhelios.plugins status
    python -m pyhelios.plugins discover  
    python -m pyhelios.plugins info <plugin_name>
    python -m pyhelios.plugins validate <plugin_list>
"""

import sys
import argparse
from pathlib import Path

# Add pyhelios to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyhelios.plugins import print_plugin_status, get_plugin_info
from pyhelios.plugins.registry import get_plugin_registry
from pyhelios.config.plugin_metadata import PLUGIN_METADATA, get_all_plugin_names, get_platform_compatible_plugins
from pyhelios.config.dependency_resolver import PluginDependencyResolver


def cmd_status(args):
    """Show comprehensive plugin status."""
    print_plugin_status()


def cmd_discover(args):
    """Discover and recommend optimal plugin configuration."""
    print("PyHelios Plugin Discovery")
    print("=" * 25)
    
    resolver = PluginDependencyResolver()
    
    # Check system capabilities
    print("System Analysis:")
    print("-" * 15)
    
    # Platform compatibility
    compatible_plugins = get_platform_compatible_plugins()
    all_plugins = get_all_plugin_names()
    platform_compatibility = len(compatible_plugins) / len(all_plugins) * 100
    print(f"Platform compatibility: {platform_compatibility:.1f}% ({len(compatible_plugins)}/{len(all_plugins)} plugins)")
    
    # GPU availability
    gpu_available = resolver._check_cuda()
    print(f"GPU/CUDA support: {'✓ Available' if gpu_available else '✗ Not available'}")
    
    # System dependencies
    system_deps = resolver._check_system_dependencies(compatible_plugins)
    available_deps = sum(1 for available in system_deps.values() if available)
    total_deps = len(system_deps)
    if total_deps > 0:
        dep_percentage = available_deps / total_deps * 100
        print(f"System dependencies: {dep_percentage:.1f}% available ({available_deps}/{total_deps})")
    
    print()
    
    # Recommend configuration
    print("Recommendations:")
    print("-" * 15)
    
    if gpu_available:
        print("✓ GPU detected - GPU-accelerated workflows are possible")
        print("  Recommended for: Ray tracing, radiation modeling, high-performance simulations")
        recommended_plugins = ["weberpenntree", "canopygenerator", "solarposition", "radiation", "visualizer", "energybalance"]
    else:
        print("• No GPU detected - Using CPU-based workflows")
        print("  Recommended for: General plant modeling, visualization, basic simulations")
        recommended_plugins = ["weberpenntree", "canopygenerator", "solarposition", "visualizer", "energybalance"]
    
    # Filter by platform compatibility
    recommended_plugins = [p for p in recommended_plugins if p in compatible_plugins]
    validation = resolver.validate_configuration(recommended_plugins)
    
    print(f"\nRecommended plugins ({len(recommended_plugins)}):")
    for plugin in recommended_plugins:
        if plugin in validation['platform_compatible']:
            print(f"  ✓ {plugin}")
        else:
            print(f"  ⚠ {plugin} (may have compatibility issues)")
    
    # Show build command
    print(f"\nSuggested build command:")
    plugin_list = ",".join(recommended_plugins)
    print(f"  build_scripts/build_helios --plugins {plugin_list}")
    
    # Show potential issues
    if validation['platform_incompatible']:
        print(f"\n⚠ Platform compatibility issues:")
        for plugin in validation['platform_incompatible']:
            print(f"  - {plugin}")
    
    missing_system_deps = [dep for dep, available in system_deps.items() if not available]
    if missing_system_deps:
        print(f"\n⚠ Missing system dependencies:")
        for dep in missing_system_deps:
            print(f"  - {dep}")


def cmd_info(args):
    """Show detailed information about a specific plugin."""
    plugin_name = args.plugin_name
    
    if plugin_name not in PLUGIN_METADATA:
        print(f"❌ Unknown plugin: {plugin_name}")
        print(f"Available plugins: {', '.join(sorted(get_all_plugin_names()))}")
        return 1
    
    info = get_plugin_info(plugin_name)
    metadata = PLUGIN_METADATA[plugin_name]
    
    print(f"Plugin Information: {plugin_name}")
    print("=" * (20 + len(plugin_name)))
    
    print(f"Description: {metadata.description}")
    print(f"GPU Required: {'Yes' if metadata.gpu_required else 'No'}")
    print(f"Optional: {'Yes' if metadata.optional else 'No (core plugin)'}")
    print(f"Supported Platforms: {', '.join(metadata.platforms)}")
    
    if metadata.system_dependencies:
        print(f"System Dependencies: {', '.join(metadata.system_dependencies)}")
    
    if metadata.plugin_dependencies:
        print(f"Plugin Dependencies: {', '.join(metadata.plugin_dependencies)}")
    
    
    # Runtime availability
    print(f"\nRuntime Status:")
    if 'error' in info:
        print(f"❌ Error: {info['error']}")
    else:
        print(f"Available: {'✓ Yes' if info['available'] else '✗ No'}")
        
        if info.get('validation'):
            validation = info['validation']
            print(f"Validation: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
            if not validation['valid']:
                print(f"  Reason: {validation['reason']}")
            
            if validation['missing_dependencies']:
                print(f"  Missing dependencies: {', '.join(validation['missing_dependencies'])}")
    
    
    return 0


def cmd_validate(args):
    """Validate a list of plugins."""
    if args.plugins:
        plugins = args.plugins
    else:
        # Read from stdin or prompt
        plugins_input = input("Enter plugins (comma-separated): ").strip()
        plugins = [p.strip() for p in plugins_input.split(',') if p.strip()]
    
    if not plugins:
        print("❌ No plugins specified")
        return 1
    
    print(f"Validating plugins: {', '.join(plugins)}")
    print("=" * 40)
    
    resolver = PluginDependencyResolver()
    validation = resolver.validate_configuration(plugins)
    
    print(f"Total requested: {len(plugins)}")
    print(f"Valid plugins: {len(validation['valid_plugins'])}")
    print(f"Invalid plugins: {len(validation['invalid_plugins'])}")
    print(f"Platform compatible: {len(validation['platform_compatible'])}")
    print(f"Platform incompatible: {len(validation['platform_incompatible'])}")
    
    if validation['invalid_plugins']:
        print(f"\n❌ Invalid plugins:")
        for plugin in validation['invalid_plugins']:
            print(f"  - {plugin}")
    
    if validation['platform_incompatible']:
        print(f"\n⚠ Platform incompatible:")
        for plugin in validation['platform_incompatible']:
            print(f"  - {plugin}")
    
    if validation['system_dependencies']:
        print(f"\nSystem Dependencies:")
        for dep, available in validation['system_dependencies'].items():
            status = "✓" if available else "✗"
            print(f"  {status} {dep}")
    
    print(f"\nGPU required: {'Yes' if validation['gpu_required'] else 'No'}")
    
    # Provide suggestions
    if validation['invalid_plugins'] or validation['platform_incompatible']:
        print(f"\n💡 Suggestions:")
        print(f"  - Use only valid, platform-compatible plugins")
        print(f"  - Check available plugins: python -m pyhelios.plugins status")
        print(f"  - Use specific plugin selection: build_scripts/build_helios --plugins plugin1,plugin2")
        return 1
    else:
        print(f"\n✅ Configuration is valid")
        return 0




def main():
    """Main entry point for plugin command-line interface."""
    parser = argparse.ArgumentParser(
        description="PyHelios plugin status and discovery tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status       Show comprehensive plugin status
  discover     Analyze system and recommend optimal configuration  
  info         Show detailed information about a specific plugin
  validate     Validate a list of plugins for compatibility

Examples:
  python -m pyhelios.plugins status
  python -m pyhelios.plugins discover
  python -m pyhelios.plugins info radiation
  python -m pyhelios.plugins validate --plugins radiation,visualizer
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show plugin status')
    status_parser.set_defaults(func=cmd_status)
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover optimal configuration')
    discover_parser.set_defaults(func=cmd_discover)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show plugin information')
    info_parser.add_argument('plugin_name', help='Name of the plugin')
    info_parser.set_defaults(func=cmd_info)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate plugin configuration')
    validate_parser.add_argument('--plugins', nargs='*', help='Plugin names to validate')
    validate_parser.set_defaults(func=cmd_validate)
    
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())