#!/usr/bin/env node

/**
 * CROAK CLI - Computer Recognition Orchestration Agent Kit
 * Main entry point for the croak command
 *
 * This CLI handles installation/setup commands (init, doctor, upgrade)
 * and passes through all other commands to the Python croak package.
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, existsSync } from 'fs';
import { spawn, execFileSync } from 'child_process';

// Import commands
import { initCommand } from '../src/commands/init.js';
import { doctorCommand } from '../src/commands/doctor.js';
import { upgradeCommand } from '../src/commands/upgrade.js';

// Get package version
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packageJson = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf8'));

// ASCII Art Banner
const banner = chalk.green(`
   ____ ____   ___    _    _  __
  / ___|  _ \\ / _ \\  / \\  | |/ /
 | |   | |_) | | | |/ _ \\ | ' /
 | |___|  _ <| |_| / ___ \\| . \\
  \\____|_| \\_\\\\___/_/   \\_\\_|\\_\\

  ${chalk.cyan('Computer Recognition Orchestration Agent Kit')}
  ${chalk.dim('by vfrog.ai')}
`);

// Commands handled by this JS CLI (installation/setup)
const JS_COMMANDS = ['init', 'doctor', 'upgrade', 'help', '-h', '--help', '-v', '--version'];

// Check if this is a command we handle in JS or should pass to Python
const args = process.argv.slice(2);
const firstArg = args[0];

// If it's a Python command, pass through to Python CLI
if (firstArg && !JS_COMMANDS.includes(firstArg) && !firstArg.startsWith('-')) {
  // Try to find the Python-installed croak binary.
  // IMPORTANT: We must not fall back to bare 'croak' because that resolves
  // to THIS Node.js script, causing an infinite recursive spawn loop.
  const pythonCommands = [
    // Check if in a virtual environment
    join(process.cwd(), '.venv', 'bin', 'croak'),
    join(process.cwd(), 'venv', 'bin', 'croak'),
  ];

  let pythonCroakPath = null;

  // For Windows compatibility
  if (process.platform === 'win32') {
    pythonCommands.unshift(
      join(process.cwd(), '.venv', 'Scripts', 'croak.exe'),
      join(process.cwd(), 'venv', 'Scripts', 'croak.exe')
    );
  }

  // Also check if Python croak is installed via pip (not this Node.js script)
  try {
    const pipShowOutput = execFileSync('python3', ['-c', 'import croak; print(croak.__file__)'], {
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    if (pipShowOutput.trim()) {
      // Python croak package is installed — invoke via python -m
      pythonCroakPath = '__python_module__';
    }
  } catch {
    // Python croak not installed as a package
  }

  // Find the Python croak command from venv paths
  if (!pythonCroakPath) {
    for (const cmd of pythonCommands) {
      if (existsSync(cmd)) {
        pythonCroakPath = cmd;
        break;
      }
    }
  }

  if (pythonCroakPath) {
    // Pass through to Python CLI
    let spawnCmd, spawnArgs;
    if (pythonCroakPath === '__python_module__') {
      spawnCmd = 'python3';
      spawnArgs = ['-m', 'croak', ...args];
    } else {
      spawnCmd = pythonCroakPath;
      spawnArgs = args;
    }
    const child = spawn(spawnCmd, spawnArgs, {
      stdio: 'inherit',
      shell: process.platform === 'win32',
    });

    child.on('close', (code) => {
      process.exit(code);
    });

    child.on('error', (err) => {
      if (err.code === 'ENOENT') {
        console.log(chalk.red('\nCROAK Python package not found.'));
        console.log(chalk.yellow('Run `croak init` to set up CROAK first.\n'));
        console.log('Or install manually:');
        console.log(chalk.cyan('  pip install croak-cv\n'));
      } else {
        console.error(chalk.red(`Error: ${err.message}`));
      }
      process.exit(1);
    });
  } else {
    console.log(chalk.red('\nCROAK Python package not found.'));
    console.log(chalk.yellow('Run `croak init` to set up CROAK first.\n'));
    console.log('Or install manually:');
    console.log(chalk.cyan('  pip install croak-cv\n'));
    process.exit(1);
  }
} else {
  // Handle JS commands (init, doctor, upgrade, help)
  const program = new Command();

  program
    .name('croak')
    .description('CROAK - Agentic framework for object detection model development')
    .version(packageJson.version, '-v, --version', 'Output the current version')
    .addHelpText('beforeAll', banner);

  // Register commands
  program
    .command('init')
    .description('Initialize CROAK in the current directory')
    .option('-y, --yes', 'Skip prompts and use defaults')
    .option('--name <name>', 'Project name')
    .option('--no-vfrog', 'Skip vfrog.ai integration setup')
    .option('--no-modal', 'Skip Modal.com GPU setup')
    .action(initCommand);

  program
    .command('doctor')
    .description('Check environment and dependencies')
    .option('--fix', 'Attempt to fix issues automatically')
    .action(doctorCommand);

  program
    .command('upgrade')
    .description('Upgrade CROAK to the latest version')
    .option('--check', 'Check for updates without installing')
    .action(upgradeCommand);

  // Help with additional info about Python commands
  program
    .command('help [command]')
    .description('Display help for a command')
    .action((cmd) => {
      if (cmd) {
        const subCommand = program.commands.find((c) => c.name() === cmd);
        if (subCommand) {
          subCommand.outputHelp();
        } else {
          // Maybe it's a Python command
          console.log(chalk.yellow(`'${cmd}' is handled by the Python CLI.`));
          console.log(chalk.dim('Run: croak ' + cmd + ' --help\n'));
        }
      } else {
        program.outputHelp();
        console.log(chalk.cyan('\n📦 Setup Commands (this CLI):'));
        console.log('  init      Initialize CROAK in current directory');
        console.log('  doctor    Check environment and dependencies');
        console.log('  upgrade   Upgrade CROAK to latest version');
        console.log(chalk.cyan('\n🐍 ML Commands (Python CLI - requires `croak init` first):'));
        console.log('  scan      Scan directory for images and annotations');
        console.log('  validate  Validate data quality');
        console.log('  split     Create train/val/test splits');
        console.log('  prepare   Full data preparation pipeline');
        console.log('  train     Start model training');
        console.log('  evaluate  Run model evaluation');
        console.log('  export    Export model to deployment format');
        console.log('  deploy    Deploy model to cloud or edge');
        console.log('  status    Show pipeline status');
        console.log(chalk.dim('\nRun `croak <command> --help` for more info on a command.\n'));
      }
    });

  // Custom help formatting
  program.configureHelp({
    sortSubcommands: true,
    subcommandTerm: (cmd) => chalk.cyan(cmd.name()) + ' ' + chalk.dim(cmd.usage()),
  });

  // Error handling
  program.showHelpAfterError('(add --help for additional information)');

  // Parse arguments
  program.parse(process.argv);

  // Show help if no command provided
  if (!process.argv.slice(2).length) {
    console.log(banner);
    console.log(chalk.yellow('Run `croak init` to get started!\n'));
    program.outputHelp();
    console.log(chalk.cyan('\n🐍 ML Commands (available after `croak init`):'));
    console.log('  scan, validate, split, prepare, train, evaluate, export, deploy, status');
    console.log(chalk.dim('\nRun `croak <command> --help` for more info.\n'));
  }
}
