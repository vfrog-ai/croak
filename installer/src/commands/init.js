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
import { checkVfrogCLI, checkVfrogAuth, checkVfrogContext } from '../utils/vfrog-setup.js';
import { getIDEChoices, getIDEConfig } from '../utils/ide-setup.js';
import { generateAllCommands } from '../utils/command-generator.js';
import { generateClaudeMd } from '../utils/claude-md-generator.js';
import { DEFAULT_CONFIG, DEFAULT_STATE, CROAK_DIR } from '../index.js';

/**
 * Available agent modules for selection
 */
const AGENT_MODULES = [
  {
    name: 'router',
    message: 'Router (Pipeline Coordinator) — always included',
    value: 'router',
    disabled: true,
    hint: 'Required',
  },
  {
    name: 'data',
    message: 'Data Agent (Scout) — scanning, validation, preparation',
    value: 'data',
  },
  {
    name: 'training',
    message: 'Training Agent (Coach) — model training, experiments',
    value: 'training',
  },
  {
    name: 'evaluation',
    message: 'Evaluation Agent (Judge) — model evaluation, analysis',
    value: 'evaluation',
  },
  {
    name: 'deployment',
    message: 'Deployment Agent (Shipper) — export, deployment',
    value: 'deployment',
  },
];

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
  let ideSelection = ['claude-code']; // Default to Claude Code
  let agentSelection = ['router', 'data', 'training', 'evaluation', 'deployment']; // All agents

  if (!options.yes) {
    const result = await gatherConfiguration(options);
    config = result.config;
    ideSelection = result.ideSelection;
    agentSelection = result.agentSelection;
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

    // Generate IDE commands (NEW STEP)
    for (const ide of ideSelection) {
      spinner.start(`Generating ${getIDEConfig(ide).name} commands...`);
      try {
        const result = generateAllCommands(ide, { selectedAgents: agentSelection });
        spinner.succeed(
          `${getIDEConfig(ide).name} commands generated (${result.agents.length} agents, ${result.workflows.length} workflows)`
        );
      } catch (error) {
        spinner.warn(`${getIDEConfig(ide).name} command generation had issues: ${error.message}`);
      }
    }

    // Generate CLAUDE.md (NEW STEP)
    if (ideSelection.includes('claude-code')) {
      spinner.start('Generating CLAUDE.md project context...');
      try {
        generateClaudeMd(config, { overwrite: true });
        spinner.succeed('CLAUDE.md generated');
      } catch (error) {
        spinner.warn(`CLAUDE.md generation had issues: ${error.message}`);
      }
    }

    // Check vfrog CLI integration
    if (options.vfrog !== false) {
      spinner.start('Checking vfrog CLI...');
      const cliInstalled = await checkVfrogCLI();
      if (cliInstalled) {
        spinner.succeed('vfrog CLI found');

        spinner.start('Checking vfrog authentication...');
        const isAuth = await checkVfrogAuth();
        if (isAuth) {
          spinner.succeed('vfrog authenticated');

          spinner.start('Checking vfrog context...');
          const ctx = await checkVfrogContext();
          if (ctx.configured) {
            spinner.succeed('vfrog context configured (org + project set)');
          } else {
            spinner.warn('vfrog context not set. Run `croak vfrog setup` to select org/project.');
          }
        } else {
          spinner.warn('vfrog not authenticated. Run `croak vfrog setup` to login.');
        }
      } else {
        spinner.warn('vfrog CLI not installed. Download from: https://github.com/vfrog/vfrog-cli/releases');
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
    printSuccess(config, ideSelection, agentSelection);
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

  // IDE Selection (NEW STEP)
  console.log('');
  const ideChoices = getIDEChoices();
  let ideSelection = ['claude-code']; // Default

  if (ideChoices.length > 0) {
    const { selectedIDEs } = await prompt({
      type: 'multiselect',
      name: 'selectedIDEs',
      message: 'Which AI coding tools do you use?',
      choices: ideChoices.map((ide) => ({
        name: ide.value,
        message: ide.message,
        value: ide.value,
      })),
      initial: ['claude-code'],
      hint: 'Space to select, Enter to confirm',
    });

    if (selectedIDEs && selectedIDEs.length > 0) {
      ideSelection = selectedIDEs;
    }
  }

  // Module/Agent Selection (NEW STEP)
  console.log('');
  const { selectedAgents } = await prompt({
    type: 'multiselect',
    name: 'selectedAgents',
    message: 'Which CROAK agents do you want to enable?',
    choices: AGENT_MODULES,
    initial: ['data', 'training', 'evaluation', 'deployment'],
    hint: 'Space to select, Enter to confirm',
  });

  // Always include router
  const agentSelection = ['router', ...(selectedAgents || [])];

  return { config, ideSelection, agentSelection };
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
function printSuccess(config, ideSelection = [], agentSelection = []) {
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

  // Show IDE integration info (NEW)
  if (ideSelection.includes('claude-code')) {
    console.log(chalk.green('✓ Claude Code integration enabled'));
    console.log('');
    console.log(chalk.yellow('Slash commands available:\n'));
    console.log(chalk.cyan('  Agents:'));
    if (agentSelection.includes('router'))
      console.log('    /croak-router      ' + chalk.dim('Pipeline coordinator'));
    if (agentSelection.includes('data'))
      console.log('    /croak-data        ' + chalk.dim('Data quality specialist'));
    if (agentSelection.includes('training'))
      console.log('    /croak-training    ' + chalk.dim('Training configuration'));
    if (agentSelection.includes('evaluation'))
      console.log('    /croak-evaluation  ' + chalk.dim('Model evaluation'));
    if (agentSelection.includes('deployment'))
      console.log('    /croak-deployment  ' + chalk.dim('Deployment & export'));

    console.log('');
    console.log(chalk.cyan('  Workflows:'));
    console.log('    /croak-data-preparation   ' + chalk.dim('Full data pipeline'));
    console.log('    /croak-model-training     ' + chalk.dim('Training pipeline'));
    console.log('    /croak-model-evaluation   ' + chalk.dim('Evaluation pipeline'));
    console.log('    /croak-model-deployment   ' + chalk.dim('Deployment pipeline'));
    console.log('');
  }

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

  if (ideSelection.includes('claude-code')) {
    console.log(
      chalk.dim('  Tip: Open Claude Code and type /croak-router to get started with guidance!')
    );
    console.log('');
  }

  if (!config.vfrog) {
    console.log(chalk.dim('  Note: vfrog integration disabled. Install CLI and run `croak vfrog setup` to enable.'));
  }

  console.log(chalk.dim('\n  For help, run: croak help'));
  console.log(chalk.dim('  Documentation: https://github.com/vfrog-ai/croak\n'));
}
