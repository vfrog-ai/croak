/**
 * CROAK upgrade command
 * Upgrade CROAK to the latest version
 */

import chalk from 'chalk';
import ora from 'ora';
import semver from 'semver';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

import { CROAK_DIR } from '../index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Upgrade CROAK to the latest version
 */
export async function upgradeCommand(options) {
  console.log(chalk.cyan('\n🔄 CROAK Upgrade Check\n'));

  // Get current version
  const packageJsonPath = join(__dirname, '..', '..', 'package.json');
  const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'));
  const currentVersion = packageJson.version;

  console.log(chalk.dim(`Current version: ${currentVersion}`));

  // Check for updates
  const spinner = ora('Checking for updates...').start();

  try {
    const latestVersion = await getLatestVersion();

    if (semver.gt(latestVersion, currentVersion)) {
      spinner.succeed(`New version available: ${latestVersion}`);
      console.log('');

      if (options.check) {
        // Just check, don't install
        printUpgradeInfo(currentVersion, latestVersion);
        return;
      }

      // Perform upgrade
      await performUpgrade(latestVersion);
    } else {
      spinner.succeed('You are on the latest version!');
      console.log(chalk.green(`\n✨ CROAK ${currentVersion} is up to date.\n`));
    }
  } catch (error) {
    spinner.fail('Failed to check for updates');
    console.error(chalk.red(`\nError: ${error.message}`));
    console.log(chalk.dim('\nTry manually: npm update -g croak-cv'));
    process.exit(1);
  }
}

/**
 * Get the latest version from npm
 */
async function getLatestVersion() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('npm', ['view', 'croak-cv', 'version']);
    return stdout.trim();
  } catch {
    // If not published yet, return current version
    return '0.1.0';
  }
}

/**
 * Print upgrade information
 */
function printUpgradeInfo(currentVersion, latestVersion) {
  console.log(chalk.yellow('Upgrade available!\n'));
  console.log(`  Current: ${chalk.dim(currentVersion)}`);
  console.log(`  Latest:  ${chalk.green(latestVersion)}`);
  console.log('');
  console.log(chalk.cyan('To upgrade, run:'));
  console.log(chalk.white('  npm update -g croak-cv'));
  console.log('');
  console.log(chalk.dim('Or run `croak upgrade` without --check to upgrade automatically.'));
  console.log('');
}

/**
 * Perform the upgrade
 */
async function performUpgrade(latestVersion) {
  const { execa } = await import('execa');
  const { prompt } = await import('enquirer');

  // Confirm upgrade
  const { confirmUpgrade } = await prompt({
    type: 'confirm',
    name: 'confirmUpgrade',
    message: `Upgrade to version ${latestVersion}?`,
    initial: true,
  });

  if (!confirmUpgrade) {
    console.log(chalk.dim('\nUpgrade cancelled.'));
    return;
  }

  // Check if project needs migration
  if (existsSync(CROAK_DIR)) {
    console.log(chalk.yellow('\n⚠️  Existing CROAK project detected.'));
    console.log(chalk.dim('  Your configuration will be preserved.'));
    console.log(chalk.dim('  Agent definitions may be updated.\n'));
  }

  // Perform upgrade
  const spinner = ora('Upgrading CROAK...').start();

  try {
    await execa('npm', ['install', '-g', 'croak-cv@latest']);
    spinner.succeed('CROAK upgraded successfully!');

    // Update local project if exists
    if (existsSync(CROAK_DIR)) {
      spinner.start('Updating project files...');
      await updateProjectFiles();
      spinner.succeed('Project files updated');
    }

    console.log(chalk.green(`\n✨ Successfully upgraded to CROAK ${latestVersion}!\n`));

    // Show changelog
    console.log(chalk.cyan("What's new:"));
    console.log(chalk.dim('  See https://github.com/vfrog-ai/croak/releases\n'));
  } catch (error) {
    spinner.fail('Upgrade failed');
    throw error;
  }
}

/**
 * Update project files after upgrade
 */
async function updateProjectFiles() {
  const { copyTemplates } = await import('../utils/template-copy.js');

  // Backup existing agents
  const agentsDir = join(CROAK_DIR, 'agents');
  const backupDir = join(CROAK_DIR, 'agents.backup');

  if (existsSync(agentsDir)) {
    const { cpSync, rmSync } = await import('fs');

    // Create backup
    if (existsSync(backupDir)) {
      rmSync(backupDir, { recursive: true });
    }
    cpSync(agentsDir, backupDir, { recursive: true });
  }

  // Copy new templates (this would update agents, workflows, etc.)
  await copyTemplates(CROAK_DIR);
}
