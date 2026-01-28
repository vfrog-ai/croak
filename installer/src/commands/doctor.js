/**
 * CROAK doctor command
 * Check environment and dependencies
 */

import chalk from 'chalk';
import ora from 'ora';
import { existsSync } from 'fs';
import { join } from 'path';

import { checkPython, getPythonVersion, checkPythonPackage } from '../utils/python-check.js';
import { checkVfrogKey } from '../utils/vfrog-setup.js';
import { CROAK_DIR } from '../index.js';

/**
 * Check environment and dependencies
 */
export async function doctorCommand(options) {
  console.log(chalk.cyan('\n🔍 CROAK Doctor - Environment Check\n'));

  const issues = [];
  const warnings = [];

  // Check CROAK initialization
  console.log(chalk.bold('Project Status'));
  console.log(chalk.dim('─'.repeat(40)));

  if (existsSync(CROAK_DIR)) {
    printCheck('CROAK initialized', true);

    // Check config file
    const configExists = existsSync(join(CROAK_DIR, 'config.yaml'));
    printCheck('Configuration file', configExists);
    if (!configExists) issues.push('Missing config.yaml');

    // Check state file
    const stateExists = existsSync(join(CROAK_DIR, 'pipeline-state.yaml'));
    printCheck('Pipeline state file', stateExists);
    if (!stateExists) warnings.push('Missing pipeline-state.yaml');

    // Check agents
    const agentsExist = existsSync(join(CROAK_DIR, 'agents'));
    printCheck('Agent definitions', agentsExist);
    if (!agentsExist) issues.push('Missing agents directory');

  } else {
    printCheck('CROAK initialized', false);
    issues.push('CROAK not initialized. Run `croak init` first.');
  }

  console.log('');

  // Check Python environment
  console.log(chalk.bold('Python Environment'));
  console.log(chalk.dim('─'.repeat(40)));

  const pythonOk = await checkPython();
  if (pythonOk) {
    const version = await getPythonVersion();
    printCheck(`Python ${version}`, true);

    // Check key packages
    const packages = [
      { name: 'ultralytics', required: true },
      { name: 'torch', required: true },
      { name: 'modal', required: false },
      { name: 'mlflow', required: false },
      { name: 'pydantic', required: true },
      { name: 'pyyaml', required: true }
    ];

    for (const pkg of packages) {
      const installed = await checkPythonPackage(pkg.name);
      printCheck(`  ${pkg.name}`, installed, pkg.required ? 'required' : 'optional');

      if (!installed && pkg.required) {
        issues.push(`Missing required package: ${pkg.name}`);
      } else if (!installed && !pkg.required) {
        warnings.push(`Optional package not installed: ${pkg.name}`);
      }
    }
  } else {
    printCheck('Python 3.10+', false);
    issues.push('Python 3.10 or higher required');
  }

  console.log('');

  // Check GPU
  console.log(chalk.bold('GPU & Compute'));
  console.log(chalk.dim('─'.repeat(40)));

  const gpuCheck = await checkGPU();
  if (gpuCheck.available) {
    printCheck(`NVIDIA GPU (${gpuCheck.name})`, true);
    printCheck(`  CUDA ${gpuCheck.cuda}`, true);
    printCheck(`  VRAM: ${gpuCheck.vram}`, gpuCheck.vramOk);
    if (!gpuCheck.vramOk) {
      warnings.push('GPU VRAM less than 8GB - may need cloud GPU for larger models');
    }
  } else {
    printCheck('Local NVIDIA GPU', false, 'optional');
    console.log(chalk.dim('    Will use Modal.com for GPU training'));
  }

  // Check Modal
  const modalInstalled = await checkPythonPackage('modal');
  if (modalInstalled) {
    const modalConfigured = await checkModalSetup();
    printCheck('Modal.com configured', modalConfigured);
    if (!modalConfigured) {
      warnings.push('Modal.com not configured. Run `modal setup` for cloud GPU access.');
    }
  } else {
    printCheck('Modal.com SDK', false, 'recommended');
    warnings.push('Modal.com SDK not installed. Run `pip install modal` for cloud GPU.');
  }

  console.log('');

  // Check Integrations
  console.log(chalk.bold('Integrations'));
  console.log(chalk.dim('─'.repeat(40)));

  // vfrog
  const vfrogKey = await checkVfrogKey();
  printCheck('vfrog.ai API key', vfrogKey);
  if (!vfrogKey) {
    warnings.push('vfrog.ai API key not set. Required for annotation features.');
  }

  // Git
  const gitOk = await checkGit();
  printCheck('Git', gitOk, 'recommended');
  if (!gitOk) {
    warnings.push('Git not found. Recommended for version control.');
  }

  console.log('');

  // Summary
  console.log(chalk.bold('Summary'));
  console.log(chalk.dim('─'.repeat(40)));

  if (issues.length === 0 && warnings.length === 0) {
    console.log(chalk.green('\n✨ All checks passed! Your environment is ready.\n'));
  } else {
    if (issues.length > 0) {
      console.log(chalk.red(`\n❌ ${issues.length} issue(s) found:\n`));
      issues.forEach(issue => {
        console.log(chalk.red(`   • ${issue}`));
      });
    }

    if (warnings.length > 0) {
      console.log(chalk.yellow(`\n⚠️  ${warnings.length} warning(s):\n`));
      warnings.forEach(warning => {
        console.log(chalk.yellow(`   • ${warning}`));
      });
    }

    console.log('');
  }

  // Fix option
  if (options.fix && issues.length > 0) {
    console.log(chalk.cyan('\n🔧 Attempting automatic fixes...\n'));
    await attemptFixes(issues);
  }

  // Exit code based on issues
  if (issues.length > 0) {
    process.exit(1);
  }
}

/**
 * Print a check result
 */
function printCheck(label, passed, optional = null) {
  const icon = passed ? chalk.green('✓') : (optional ? chalk.yellow('○') : chalk.red('✗'));
  const suffix = optional && !passed ? chalk.dim(` (${optional})`) : '';
  console.log(`  ${icon} ${label}${suffix}`);
}

/**
 * Check for NVIDIA GPU
 */
async function checkGPU() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('nvidia-smi', [
      '--query-gpu=name,driver_version,memory.total',
      '--format=csv,noheader,nounits'
    ]);

    const [name, driver, vram] = stdout.trim().split(', ');
    const vramGB = parseInt(vram) / 1024;

    return {
      available: true,
      name: name.trim(),
      cuda: driver.trim(),
      vram: `${vramGB.toFixed(1)}GB`,
      vramOk: vramGB >= 8
    };
  } catch {
    return { available: false };
  }
}

/**
 * Check Modal.com setup
 */
async function checkModalSetup() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('modal', ['token', 'show'], { reject: false });
    return stdout.includes('Token') || stdout.includes('authenticated');
  } catch {
    return false;
  }
}

/**
 * Check Git installation
 */
async function checkGit() {
  const { execa } = await import('execa');

  try {
    await execa('git', ['--version']);
    return true;
  } catch {
    return false;
  }
}

/**
 * Attempt to fix issues automatically
 */
async function attemptFixes(issues) {
  const { execa } = await import('execa');

  for (const issue of issues) {
    if (issue.includes('Missing required package')) {
      const pkg = issue.split(': ')[1];
      const spinner = ora(`Installing ${pkg}...`).start();

      try {
        await execa('pip', ['install', pkg]);
        spinner.succeed(`Installed ${pkg}`);
      } catch (error) {
        spinner.fail(`Failed to install ${pkg}: ${error.message}`);
      }
    }

    if (issue.includes('not initialized')) {
      console.log(chalk.yellow('  Run `croak init` to initialize the project.'));
    }
  }
}
