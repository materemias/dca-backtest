# Python Code Organization Rules

## File Guidelines
- Maximum file length: 250 lines
- Minimum file length: 50 lines (unless necessary)
- Split files based on logical functionality
- Maintain code cohesion when splitting

## When and How to Split
- Split at natural break points:
  - UI components vs business logic
  - Core functionality vs utilities
  - Different feature domains
- Use clear, descriptive file names
- Keep dependencies clean and minimal
- Document file purposes

## What to Avoid
- Files with mixed responsibilities
- Splitting tightly coupled code
- Circular dependencies
- Over-fragmenting features
- Arbitrary splits that break logical flow
