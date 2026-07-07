# Contributing to AI Email Suggested Response System

Thank you for your interest in contributing! We welcome code contributions, issue reports, feature requests, and improvements to the evaluation metrics.

## Code Style & Standards

- **Python (Backend)**: Follow PEP 8 guidelines. Use Ruff or Black for linting and formatting. Ensure static types are checked via MyPy.
- **TypeScript & React (Frontend)**: Follow strict TypeScript guidelines. Verify there are no unused imports, variables, or type definitions.
- **Testing**: Add unit tests for any new evaluation metrics under `backend/tests/` and verify endpoints via HTTP test clients.

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Install dependencies for both frontend and backend.
3. Verify that the end-to-end verification script passes:
   ```bash
   python scripts/test_pipeline.py
   ```
4. Commit your changes using descriptive commit messages.
5. Push to your fork and submit a Pull Request.
