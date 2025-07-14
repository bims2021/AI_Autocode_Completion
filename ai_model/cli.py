
"""
Command Line Interface for AI Model
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from . import AIModel, load_model, complete_code, analyze_code
from .utils import ModelUtils
from .exceptions import AIModelException

def setup_argument_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(
        description="AI Model for Code Completion and Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Complete code')
    complete_parser.add_argument('input', help='Input code file or string')
    complete_parser.add_argument('--language', '-l', default='python', help='Programming language')
    complete_parser.add_argument('--model', '-m', default='codegpt', help='Model to use')
    complete_parser.add_argument('--output', '-o', help='Output file')
    complete_parser.add_argument('--max-tokens', type=int, default=100, help='Maximum tokens to generate')
    complete_parser.add_argument('--temperature', type=float, default=0.7, help='Generation temperature')
    complete_parser.add_argument('--top-p', type=float, default=0.9, help='Top-p sampling')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code')
    analyze_parser.add_argument('input', help='Input code file or string')
    analyze_parser.add_argument('--language', '-l', default='python', help='Programming language')
    analyze_parser.add_argument('--model', '-m', default='codegpt', help='Model to use')
    analyze_parser.add_argument('--output', '-o', help='Output file for analysis')
    analyze_parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')
    interactive_parser.add_argument('--model', '-m', default='codegpt', help='Model to use')
    interactive_parser.add_argument('--language', '-l', default='python', help='Default programming language')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available models')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show model information')
    info_parser.add_argument('model', help='Model name')
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Log level')
    
    return parser

def read_input(input_path: str) -> str:
    """Read input from file or string"""
    if Path(input_path).exists():
        with open(input_path, 'r') as f:
            return f.read()
    else:
        return input_path

def write_output(content: str, output_path: Optional[str]):
    """Write output to file or stdout"""
    if output_path:
        with open(output_path, 'w') as f:
            f.write(content)
    else:
        print(content)

def handle_complete_command(args):
    """Handle code completion command"""
    try:
        # Read input
        code = read_input(args.input)
        
        # Generate completion
        result = complete_code(
            code,
            language=args.language,
            model_name=args.model,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p
        )
        
        # Write output
        write_output(result, args.output)
        
        if args.verbose:
            print(f"Completion generated successfully using {args.model}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_analyze_command(args):
    """Handle code analysis command"""
    try:
        # Read input
        code = read_input(args.input)
        
        # Analyze code
        result = analyze_code(
            code,
            language=args.language,
            model_name=args.model
        )
        
        # Format output
        if args.format == 'json':
            output = json.dumps(result, indent=2)
        else:
            output = format_analysis_text(result)
        
        # Write output
        write_output(output, args.output)
        
        if args.verbose:
            print(f"Analysis completed successfully using {args.model}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def format_analysis_text(analysis: dict) -> str:
    """Format analysis results as text"""
    lines = []
    lines.append(f"Language: {analysis['language']}")
    lines.append(f"Complexity: {analysis['complexity']}")
    lines.append("")
    
    metadata = analysis.get('metadata', {})
    lines.append("Metadata:")
    for key, value in metadata.items():
        lines.append(f"  {key}: {value}")
    
    structure = analysis.get('structure', {})
    if structure:
        lines.append("")
        lines.append("Structure:")
        for key, value in structure.items():
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)

def handle_interactive_command(args):
    """Handle interactive mode"""
    try:
        # Load model
        model = load_model(args.model)
        print(f"Loaded model: {args.model}")
        print("Interactive mode - Type 'exit' to quit, 'help' for commands")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'help':
                    print_interactive_help()
                elif user_input.startswith('complete '):
                    code = user_input[9:]  # Remove 'complete '
                    result = model.complete_code(code, args.language)
                    print(f"Completion: {result['completion']}")
                    print(f"Confidence: {result['confidence']:.2f}")
                elif user_input.startswith('analyze '):
                    code = user_input[8:]  # Remove 'analyze '
                    result = model.analyze_code(code, args.language)
                    print(format_analysis_text(result))
                elif user_input.startswith('lang '):
                    args.language = user_input[5:]
                    print(f"Language set to: {args.language}")
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def print_interactive_help():
    """Print interactive mode help"""
    help_text = """
Available commands:
  complete <code>  - Complete the given code
  analyze <code>   - Analyze the given code
  lang <language>  - Set the programming language
  help            - Show this help message
  exit            - Exit interactive mode
    """
    print(help_text)

def handle_list_command(args):
    """Handle list models command"""
    try:
        models = ModelUtils.get_available_models()
        
        if models:
            print("Available models:")
            for model in models:
                print(f"  - {model}")
        else:
            print("No models available")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def handle_info_command(args):
    """Handle model info command"""
    try:
        model = AIModel(args.model)
        model.load_model()
        
        info = model.get_model_info()
        
        print(f"Model: {args.model}")
        print(f"Status: {info['status']}")
        
        if 'config' in info:
            config = info['config']
            print(f"Supported languages: {', '.join(config.get('supported_languages', []))}")
            print(f"Max length: {config.get('max_length', 'Unknown')}")
            
            if 'generation_config' in config:
                gen_config = config['generation_config']
                print(f"Max new tokens: {gen_config.get('max_new_tokens', 'Unknown')}")
                print(f"Temperature: {gen_config.get('temperature', 'Unknown')}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    ModelUtils.setup_logging(args.log_level)
    
    # Load configuration if provided
    config = {}
    if args.config:
        config = ModelUtils.load_json_config(args.config)
    
    # Handle commands
    if args.command == 'complete':
        handle_complete_command(args)
    elif args.command == 'analyze':
        handle_analyze_command(args)
    elif args.command == 'interactive':
        handle_interactive_command(args)
    elif args.command == 'list':
        handle_list_command(args)
    elif args.command == 'info':
        handle_info_command(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()