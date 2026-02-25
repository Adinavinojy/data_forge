# DataForge - Offline Data Processing Pipeline

## Overview
DataForge is a high-integrity, offline-first data preprocessing system. It allows users to import datasets, apply transformations (cleaning, standardization, integration), and replay pipelines deterministically.

## Key Features
- **Offline-First**: Zero external API calls.
- **Strict Type Safety**: Prevents silent data corruption.
- **Deterministic Replay**: Pipeline hashes ensure consistency.
- **Interactive UI**: Real-time preview of data transformations.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 16+

### Quick Launch
Run the auto-start script to launch both backend and frontend:
```bash
./start_app.sh
```

### Documentation
- [User Guide](USER_GUIDE.md): How to use the application.
- [Setup Guide](SETUP_GUIDE.md): Developer setup and packaging instructions.

## License
MIT
