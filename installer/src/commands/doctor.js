/**
 * CROAK doctor command
 * Check environment and dependencies
 */

import chalk from 'chalk';
import ora from 'ora';
import { existsSync } from 'fs';
import { join } from 'path';

import { checkPython, getPythonVersion, checkPythonPackage } from '../utils/python-check.js';
import { checkVfrogCLI, getVfrogVersion, checkVfrogAuth, checkVfrogContext } from '../utils/vfrog-setup.js';
// IDE detection functions available for future use
// import { detectIDEs, getIDEConfig } from '../utils/ide-setup.js';
import { checkCompiledAgents } from '../utils/agent-compiler.js';
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
      { name: 'pyyaml', required: true },
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

  // vfrog CLI
  const vfrogInstalled = await checkVfrogCLI();
  if (vfrogInstalled) {
    const vfrogVer = await getVfrogVersion();
    printCheck(`vfrog CLI${vfrogVer ? ` (${vfrogVer})` : ''}`, true);

    const vfrogAuth = await checkVfrogAuth();
    printCheck('  vfrog authenticated', vfrogAuth);
    if (!vfrogAuth) {
      warnings.push('vfrog CLI not authenticated. Run `croak vfrog setup` to login.');
    }

    const vfrogCtx = await checkVfrogContext();
    printCheck('  vfrog context (org + project)', vfrogCtx.configured);
    if (!vfrogCtx.configured) {
      warnings.push('vfrog organisation/project not set. Run `croak vfrog setup` to configure.');
    }
  } else {
    printCheck('vfrog CLI', false, 'recommended');
    warnings.push('vfrog CLI not installed. Download from: https://github.com/vfrog/vfrog-cli/releases');
  }

  // vfrog API key (for inference)
  const vfrogApiKey = !!process.env.VFROG_API_KEY;
  printCheck('  vfrog API key (inference)', vfrogApiKey, 'optional');
  if (!vfrogApiKey) {
    warnings.push('VFROG_API_KEY not set. Needed for vfrog inference. Get key at https://platform.vfrog.ai');
  }

  // Git
  const gitOk = await checkGit();
  printCheck('Git', gitOk, 'recommended');
  if (!gitOk) {
    warnings.push('Git not found. Recommended for version control.');
  }

  console.log('');

  // Check IDE Integration (NEW)
  console.log(chalk.bold('IDE Integration'));
  console.log(chalk.dim('─'.repeat(40)));

  const ideChecks = await checkIDEIntegration();

  // Claude Code
  if (ideChecks.claudeCode.detected) {
    printCheck('Claude Code commands', ideChecks.claudeCode.commandsExist);
    if (ideChecks.claudeCode.commandsExist) {
      console.log(chalk.dim(`    ${ideChecks.claudeCode.agentCount} agents, ${ideChecks.claudeCode.workflowCount} workflows`));
    }
    if (!ideChecks.claudeCode.commandsExist) {
      warnings.push('Claude Code detected but commands not generated. Run `croak upgrade` to fix.');
    }

    printCheck('CLAUDE.md project context', ideChecks.claudeCode.claudeMdExists);
    if (!ideChecks.claudeCode.claudeMdExists) {
      warnings.push('CLAUDE.md not found. Run `croak upgrade` to generate.');
    }
  } else {
    printCheck('Claude Code', false, 'optional');
    console.log(chalk.dim('    No .claude/commands directory found'));
  }

  // Compiled agents
  const compiledStatus = checkCompiledAgents();
  if (compiledStatus.exists) {
    printCheck(`Compiled agents (${compiledStatus.count})`, !compiledStatus.needsUpdate);
    if (compiledStatus.needsUpdate) {
      warnings.push('Compiled agents out of date. Run `croak upgrade` to recompile.');
    }
  } else {
    printCheck('Compiled agents', false, 'optional');
    console.log(chalk.dim('    Run `croak upgrade` to compile agents for better reliability'));
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
      issues.forEach((issue) => {
        console.log(chalk.red(`   • ${issue}`));
      });
    }

    if (warnings.length > 0) {
      console.log(chalk.yellow(`\n⚠️  ${warnings.length} warning(s):\n`));
      warnings.forEach((warning) => {
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
  const icon = passed ? chalk.green('✓') : optional ? chalk.yellow('○') : chalk.red('✗');
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
      '--format=csv,noheader,nounits',
    ]);

    const [name, driver, vram] = stdout.trim().split(', ');
    const vramGB = parseInt(vram) / 1024;

    return {
      available: true,
      name: name.trim(),
      cuda: driver.trim(),
      vram: `${vramGB.toFixed(1)}GB`,
      vramOk: vramGB >= 8,
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
 * Check IDE integration status
 */
async function checkIDEIntegration() {
  const { readdirSync } = await import('fs');

  const result = {
    claudeCode: {
      detected: false,
      commandsExist: false,
      agentCount: 0,
      workflowCount: 0,
      claudeMdExists: false,
    },
  };

  // Check Claude Code
  // Skills are in .claude/skills/<skill-name>/SKILL.md
  const claudeSkillsDir = '.claude/skills';

  if (existsSync('.claude')) {
    result.claudeCode.detected = true;

    if (existsSync(claudeSkillsDir)) {
      const skillDirs = readdirSync(claudeSkillsDir).filter((d) =>
        d.startsWith('croak-') && existsSync(join(claudeSkillsDir, d, 'SKILL.md'))
      );

      if (skillDirs.length > 0) {
        result.claudeCode.commandsExist = true;

        // Count agents (croak-router, croak-data, etc.)
        const agentSkills = ['router', 'data', 'training', 'evaluation', 'deployment'];
        result.claudeCode.agentCount = skillDirs.filter((d) =>
          agentSkills.some((agent) => d === `croak-${agent}`)
        ).length;

        // Count workflows (croak-data-preparation, croak-model-training, etc.)
        const workflowSkills = ['data-preparation', 'model-training', 'model-evaluation', 'model-deployment'];
        result.claudeCode.workflowCount = skillDirs.filter((d) =>
          workflowSkills.some((workflow) => d === `croak-${workflow}`)
        ).length;
      }
    }
  }

  // Check CLAUDE.md
  result.claudeCode.claudeMdExists = existsSync('CLAUDE.md');

  return result;
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