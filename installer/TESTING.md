# CROAK Installer Testing Guide

This document explains how to test all CROAK commands to ensure everything works correctly.

## Quick Start

Run the comprehensive test suite:

```bash
cd installer
./test-commands.sh
```

This will test all CLI commands, linting, formatting, and package validation.

## What Gets Tested

The test script (`test-commands.sh`) verifies:

### CLI Commands
1. ✅ Version command (`--version`, `-v`)
2. ✅ Help command (`--help`, `-h`)
3. ✅ Help subcommand (`help`)
4. ✅ Init command help (`init --help`)
5. ✅ Doctor command (`doctor`) - checks environment
6. ✅ Upgrade command (`upgrade --check`, `upgrade --help`)
7. ✅ Invalid command handling (should fail gracefully)
8. ✅ No arguments (shows help/banner)

### Code Quality
9. ✅ Linting (`npm run lint`)
10. ✅ Formatting (`npm run format`)

### Package Validation
11. ✅ Package publish dry-run (`npm publish --dry-run`)
12. ✅ Package.json JSON validation
13. ✅ Required files check (package.json, bin/croak.js, src/index.js, README.md, LICENSE)

## Manual Testing

You can also test commands manually:

### Test Version
```bash
node bin/croak.js --version
```

### Test Help
```bash
node bin/croak.js --help
node bin/croak.js help
```

### Test Doctor
```bash
node bin/croak.js doctor
```

### Test Upgrade Check
```bash
node bin/croak.js upgrade --check
```

### Test Linting
```bash
npm run lint
```

### Test Formatting
```bash
npm run format
```

### Test Package Publish (Dry Run)
```bash
npm publish --dry-run
```

## Configuration Files

The following configuration files were created to support testing:

- `.eslintrc.cjs` - ESLint configuration for code linting
- `.prettierrc.json` - Prettier configuration for code formatting
- `test-commands.sh` - Comprehensive test script

## Expected Results

When all tests pass, you should see:

```
✨ All tests passed!
Tests Passed: 17
Tests Failed: 0
Total Tests: 17
```

## Troubleshooting

### Linting Errors
If linting fails, fix the issues and run:
```bash
npm run lint
```

### Formatting Issues
To auto-fix formatting:
```bash
npm run format
```

### Doctor Command
The `doctor` command may exit with code 1 if there are environment issues (missing Python packages, etc.). This is expected behavior - it's reporting issues that need to be fixed.

### Package Publish
The `npm publish --dry-run` command shows what files would be included in the published package. Make sure all required files are listed and no unwanted files (like `node_modules`) are included.

## Next Steps

After verifying all tests pass:

1. ✅ All commands work correctly
2. ✅ Code is properly linted and formatted
3. ✅ Package is ready to publish
4. ✅ All required files are present

You can now confidently publish the package with:
```bash
npm publish
```

(Note: Make sure you're authenticated with npm and have the correct permissions)
