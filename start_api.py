#!/usr/bin/env python3
"""
Start the AI Code Auditor FastAPI server.

Usage:
    python start_api.py [--model-path PATH] [--port PORT] [--load-model]
"""

import argparse
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Start AI Code Auditor API")
    parser.add_argument("--model-path", default="models/lora_adapter_v4", 
                       help="Path to LoRA adapter (default: models/lora_adapter_v4)")
    parser.add_argument("--port", type=int, default=8000, 
                       help="Port to run server on (default: 8000)")
    parser.add_argument("--load-model", action="store_true",
                       help="Load model on startup (default: False)")
    parser.add_argument("--host", default="127.0.0.1",
                       help="Host to bind to (default: 127.0.0.1)")
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["FINETUNED_MODEL_PATH"] = args.model_path
    os.environ["LOAD_MODEL_ON_STARTUP"] = "true" if args.load_model else "false"
    
    # Check if model exists
    model_path = Path(args.model_path)
    if args.load_model and not model_path.exists():
        print(f"❌ Model path not found: {model_path}")
        print(f"   Available models:")
        models_dir = Path("models")
        if models_dir.exists():
            for p in models_dir.iterdir():
                if p.is_dir() and (p / "adapter_config.json").exists():
                    print(f"   - {p}")
        else:
            print(f"   No models directory found")
        print(f"\n💡 To run without model: python start_api.py")
        print(f"   (Vector search will still work)")
        sys.exit(1)
    
    print("🚀 Starting AI Code Auditor API...")
    print(f"   Host: {args.host}:{args.port}")
    print(f"   Model: {args.model_path}")
    print(f"   Load on startup: {args.load_model}")
    print(f"   Frontend: Open frontend/index.html in browser")
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()