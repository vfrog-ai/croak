/**
 * Python environment validation utilities
 */

import { execa } from 'execa';

/**
 * Check if Python 3.10+ is available
 */
export async function checkPython() {
  try {
    const version = await getPythonVersion();
    const [major, minor] = version.split('.').map(Number);
    return major >= 3 && minor >= 10;
  } catch {
    return false;
  }
}

/**
 * Get Python version string
 */
export async function getPythonVersion() {
  // Try python3 first, then python
  const commands = ['python3', 'python'];

  for (const cmd of commands) {
    try {
      const { stdout } = await execa(cmd, ['--version']);
      const match = stdout.match(/Python (\d+\.\d+\.\d+)/);
      if (match) {
        return match[1];
      }
    } catch {
      continue;
    }
  }

  throw new Error('Python not found');
}

/**
 * Get the Python command to use
 */
export async function getPythonCommand() {
  const commands = ['python3', 'python'];

  for (const cmd of commands) {
    try {
      const { stdout } = await execa(cmd, ['--version']);
      if (stdout.includes('Python 3')) {
        return cmd;
      }
    } catch {
      continue;
    }
  }

  throw new Error('Python 3 not found');
}

/**
 * Check if a Python package is installed
 */
export async function checkPythonPackage(packageName) {
  try {
    const pythonCmd = await getPythonCommand();
    await execa(pythonCmd, ['-c', `import ${packageName}`]);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get installed version of a Python package
 */
export async function getPythonPackageVersion(packageName) {
  try {
    const pythonCmd = await getPythonCommand();
    const { stdout } = await execa(pythonCmd, [
      '-c',
      `import ${packageName}; print(${packageName}.__version__)`
    ]);
    return stdout.trim();
  } catch {
    return null;
  }
}

/**
 * Install a Python package
 */
export async function installPythonPackage(packageName) {
  const pythonCmd = await getPythonCommand();
  await execa(pythonCmd, ['-m', 'pip', 'install', packageName]);
}

/**
 * Check if running in a virtual environment
 */
export async function isInVirtualEnv() {
  try {
    const pythonCmd = await getPythonCommand();
    const { stdout } = await execa(pythonCmd, [
      '-c',
      'import sys; print(sys.prefix != sys.base_prefix)'
    ]);
    return stdout.trim() === 'True';
  } catch {
    return false;
  }
}

/**
 * Get pip command
 */
export async function getPipCommand() {
  const commands = ['pip3', 'pip'];

  for (const cmd of commands) {
    try {
      const { stdout } = await execa(cmd, ['--version']);
      if (stdout.includes('python 3') || stdout.includes('Python 3')) {
        return cmd;
      }
    } catch {
      continue;
    }
  }

  // Fall back to python -m pip
  const pythonCmd = await getPythonCommand();
  return `${pythonCmd} -m pip`;
}
