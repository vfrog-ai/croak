#!/usr/bin/env node

/**
 * CROAK CLI - Computer Recognition Orchestration Agent Kit
 * Main entry point for the croak command
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';

// Import commands
import { initCommand } from '../src/commands/init.js';
import { doctorCommand } from '../src/commands/doctor.js';
import { upgradeCommand } from '../src/commands/upgrade.js';

// Get package version
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packageJson = JSON.parse(
  readFileSync(join(__dirname, '..', 'package.json'), 'utf8')
);

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

// Create CLI program
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

// Help command (default behavior enhanced)
program
  .command('help [command]')
  .description('Display help for a command')
  .action((cmd) => {
    if (cmd) {
      const subCommand = program.commands.find(c => c.name() === cmd);
      if (subCommand) {
        subCommand.outputHelp();
      } else {
        console.log(chalk.red(`Unknown command: ${cmd}`));
        program.outputHelp();
      }
    } else {
      program.outputHelp();
    }
  });

// Custom help formatting
program.configureHelp({
  sortSubcommands: true,
  subcommandTerm: (cmd) => chalk.cyan(cmd.name()) + ' ' + chalk.dim(cmd.usage())
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
}
