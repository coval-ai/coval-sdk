import {
  closeSync,
  constants,
  fstatSync,
  ftruncateSync,
  openSync,
  readFileSync,
  writeSync,
} from 'node:fs';

function openRegularFile(filename, flags) {
  const descriptor = openSync(
    filename,
    flags | constants.O_NOFOLLOW | constants.O_NONBLOCK,
    0o644,
  );
  if (!fstatSync(descriptor).isFile()) {
    closeSync(descriptor);
    throw new Error(`Generated output must be a regular file: ${filename}`);
  }
  return descriptor;
}

function writeContents(descriptor, contents) {
  const bytes = Buffer.from(contents, 'utf8');
  let offset = 0;
  while (offset < bytes.length) {
    offset += writeSync(descriptor, bytes, offset, bytes.length - offset, offset);
  }
  ftruncateSync(descriptor, bytes.length);
}

export function readOptionalGeneratedFile(filename) {
  let descriptor;
  try {
    descriptor = openRegularFile(filename, constants.O_RDONLY);
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
  try {
    return readFileSync(descriptor, 'utf8');
  } finally {
    closeSync(descriptor);
  }
}

export function createGeneratedFile(filename, contents) {
  const descriptor = openRegularFile(
    filename,
    constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL,
  );
  try {
    writeContents(descriptor, contents);
  } finally {
    closeSync(descriptor);
  }
}

/** Keep reads and writes on one verified descriptor, even if the path changes. */
export function rewriteGeneratedFile(filename, transform) {
  let descriptor;
  try {
    descriptor = openRegularFile(filename, constants.O_RDWR);
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
  try {
    const contents = readFileSync(descriptor, 'utf8');
    const updated = transform(contents);
    if (updated === contents) return false;
    writeContents(descriptor, updated);
    return true;
  } finally {
    closeSync(descriptor);
  }
}
