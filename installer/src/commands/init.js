/**
 * CROAK init command
 * Initialize CROAK in the current directory
 */

import chalk from 'chalk';
import ora from 'ora';
import Enquirer from 'enquirer';
import { existsSync, mkdirSync, writeFileSync } from 'fs';

const { prompt } = Enquirer;
import { join } from 'path';
import yaml from 'yaml';

import { checkPython, getPythonVersion } from '../utils/python-check.js';
import { copyTemplates } from '../utils/template-copy.js';
import { checkVfrogKey } from '../utils/vfrog-setup.js';
import { DEFAULT_CONFIG, DEFAULT_STATE, CROAK_DIR } from '../index.js';

/**
 * Initialize CROAK in the current directory
 */
export async function initCommand(options) {
  console.log(chalk.cyan('\n🐸 Initializing CROAK project...\n'));

  // Check if already initialized
  if (existsSync(CROAK_DIR)) {
    const { overwrite } = await prompt({
      type: 'confirm',
      name: 'overwrite',
      message: chalk.yellow('CROAK already initialized in this directory. Overwrite?'),
      initial: false,
    });

    if (!overwrite) {
      console.log(chalk.dim('Initialization cancelled.'));
      return;
    }
  }

  // Gather configuration
  let config = { ...DEFAULT_CONFIG };

  if (!options.yes) {
    config = await gatherConfiguration(options);
  } else {
    // Use defaults with any provided options
    if (options.name) {
      config.project.name = options.name;
    } else {
      config.project.name = process.cwd().split('/').pop();
    }
  }

  // Create directory structure
  const spinner = ora('Creating directory structure...').start();

  try {
    await createDirectoryStructure(config);
    spinner.succeed('Directory structure created');

    // Copy agent templates
    spinner.start('Copying agent definitions...');
    await copyTemplates(CROAK_DIR);
    spinner.succeed('Agent definitions copied');

    // Write configuration
    spinner.start('Writing configuration...');
    writeConfiguration(config);
    spinner.succeed('Configuration written');

    // Setup vfrog if enabled
    if (options.vfrog !== false && config.vfrog?.api_key_env) {
      spinner.start('Checking vfrog.ai integration...');
      const hasVfrog = await checkVfrogKey();
      if (hasVfrog) {
        spinner.succeed('vfrog.ai integration ready');
      } else {
        spinner.warn('vfrog.ai API key not set (set VFROG_API_KEY later)');
      }
    }

    // Check Python environment
    spinner.start('Checking Python environment...');
    const pythonOk = await checkPython();
    if (pythonOk) {
      const version = await getPythonVersion();
      spinner.succeed(`Python ${version} detected`);
    } else {
      spinner.warn('Python 3.10+ required - install before training');
    }

    // Success message
    printSuccess(config);
  } catch (error) {
    spinner.fail('Initialization failed');
    console.error(chalk.red(`\nError: ${error.message}`));
    process.exit(1);
  }
}

/**
 * Gather configuration through interactive prompts
 */
async function gatherConfiguration(options) {
  const config = { ...DEFAULT_CONFIG };

  // Project name
  const { projectName } = await prompt({
    type: 'input',
    name: 'projectName',
    message: 'Project name:',
    initial: options.name || process.cwd().split('/').pop(),
    validate: (value) => value.length > 0 || 'Project name is required',
  });
  config.project.name = projectName;

  // Task type (detection only for v1)
  console.log(chalk.dim('  Task type: detection (only option in v1.0)'));
  config.project.task_type = 'detection';

  // vfrog integration
  if (options.vfrog !== false) {
    const { useVfrog } = await prompt({
      type: 'confirm',
      name: 'useVfrog',
      message: 'Enable vfrog.ai integration for annotation?',
      initial: true,
    });

    if (!useVfrog) {
      config.vfrog = null;
    }
  }

  // Modal.com for GPU
  if (options.modal !== false) {
    const { useModal } = await prompt({
      type: 'confirm',
      name: 'useModal',
      message: 'Use Modal.com for cloud GPU training?',
      initial: true,
    });

    if (!useModal) {
      config.compute.provider = 'local';
    }
  }

  // Model architecture
  const { architecture } = await prompt({
    type: 'select',
    name: 'architecture',
    message: 'Default model architecture:',
    choices: [
      { name: 'yolov8s', message: 'YOLOv8s (Recommended - balanced)' },
      { name: 'yolov8n', message: 'YOLOv8n (Fast - edge deployment)' },
      { name: 'yolov8m', message: 'YOLOv8m (Accurate - more compute)' },
      { name: 'yolov11s', message: 'YOLOv11s (Latest architecture)' },
      { name: 'rt-detr', message: 'RT-DETR (Transformer-based)' },
    ],
    initial: 0,
  });
  config.training.architecture = architecture;

  // Experiment tracking
  const { tracking } = await prompt({
    type: 'select',
    name: 'tracking',
    message: 'Experiment tracking backend:',
    choices: [
      { name: 'mlflow', message: 'MLflow (Local - recommended for starting)' },
      { name: 'wandb', message: 'Weights & Biases (Cloud - team collaboration)' },
      { name: 'none', message: 'None (Not recommended)' },
    ],
    initial: 0,
  });
  config.tracking.backend = tracking;

  // Skill level (affects verbosity)
  const { skillLevel } = await prompt({
    type: 'select',
    name: 'skillLevel',
    message: 'Your ML experience level:',
    choices: [
      { name: 'beginner', message: 'Beginner (More guidance, explanations)' },
      { name: 'intermediate', message: 'Intermediate (Balanced)' },
      { name: 'expert', message: 'Expert (Minimal prompts)' },
    ],
    initial: 1,
  });

  config.agents.verbose = skillLevel === 'beginner';
  config.agents.auto_confirm = skillLevel === 'expert';

  return config;
}

/**
 * Create the directory structure
 */
async function createDirectoryStructure(_config) {
  const directories = [
    CROAK_DIR,
    join(CROAK_DIR, 'agents'),
    join(CROAK_DIR, 'workflows'),
    join(CROAK_DIR, 'knowledge'),
    join(CROAK_DIR, 'contracts'),
    join(CROAK_DIR, 'handoffs'),
    join(CROAK_DIR, 'reports'),
    'data',
    'data/raw',
    'data/processed',
    'data/reports',
    'training',
    'training/configs',
    'training/scripts',
    'training/experiments',
    'evaluation',
    'evaluation/reports',
    'deployment',
    'deployment/edge',
  ];

  for (const dir of directories) {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }
}

/**
 * Write configuration files
 */
function writeConfiguration(config) {
  // Write config.yaml
  const configPath = join(CROAK_DIR, 'config.yaml');
  const configYaml = yaml.stringify(config, { indent: 2 });
  const configHeader = `# CROAK Configuration
# Generated by croak init
# Edit this file to customize your project settings

`;
  writeFileSync(configPath, configHeader + configYaml);

  // Write pipeline-state.yaml
  const state = {
    ...DEFAULT_STATE,
    last_updated: new Date().toISOString(),
  };
  const statePath = join(CROAK_DIR, 'pipeline-state.yaml');
  const stateYaml = yaml.stringify(state, { indent: 2 });
  const stateHeader = `# CROAK Pipeline State
# This file tracks your progress through the ML pipeline
# Do not edit manually unless you know what you're doing

`;
  writeFileSync(statePath, stateHeader + stateYaml);

  // Write .gitignore for .croak directory
  const gitignorePath = join(CROAK_DIR, '.gitignore');
  const gitignoreContent = `# CROAK gitignore
# Secrets and credentials
*.key
*.pem
secrets/

# Large files
*.pt
*.onnx
*.engine
checkpoints/

# Local state (optional - uncomment if you want to track state)
# pipeline-state.yaml

# Reports can be regenerated
# reports/
`;
  writeFileSync(gitignorePath, gitignoreContent);
}

/**
 * Print success message with next steps
 */
function printSuccess(config) {
  console.log(
    chalk.green(`
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ${chalk.bold('🐸 CROAK initialized successfully!')}                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
`)
  );

  console.log(chalk.cyan('Project: ') + config.project.name);
  console.log(chalk.cyan('Architecture: ') + config.training.architecture);
  console.log(chalk.cyan('GPU Provider: ') + config.compute.provider);
  console.log(chalk.cyan('Tracking: ') + config.tracking.backend);
  console.log('');

  console.log(chalk.yellow('Next steps:\n'));
  console.log('  1. ' + chalk.white('Add your images to') + chalk.cyan(' data/raw/'));
  console.log(
    '  2. ' + chalk.white('Run') + chalk.cyan(' croak scan') + chalk.white(' to discover your data')
  );
  console.log(
    '  3. ' +
      chalk.white('Run') +
      chalk.cyan(' croak prepare') +
      chalk.white(' to prepare your dataset')
  );
  console.log(
    '  4. ' + chalk.white('Run') + chalk.cyan(' croak train') + chalk.white(' to start training')
  );
  console.log('');

  if (!config.vfrog) {
    console.log(chalk.dim('  Note: vfrog.ai integration disabled. Enable with VFROG_API_KEY.'));
  }

  console.log(chalk.dim('\n  For help, run: croak help'));
  console.log(chalk.dim('  Documentation: https://github.com/vfrog-ai/croak\n'));
}
