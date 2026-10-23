import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, renameSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { createGeneratedFile, readOptionalGeneratedFile, rewriteGeneratedFile } from './generated-files.mjs';

function fixture(t) {
  const directory = mkdtempSync(join(tmpdir(), 'generated-files-test-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}

test('rewrites UTF-8 content, truncates old bytes, and remains idempotent', (t) => {
  const path = join(fixture(t), 'model.ts');
  createGeneratedFile(path, 'original longer value');
  assert.equal(rewriteGeneratedFile(path, () => 'é'), true);
  assert.equal(readFileSync(path, 'utf8'), 'é');
  assert.equal(rewriteGeneratedFile(path, (value) => value), false);
  assert.equal(readOptionalGeneratedFile(path), 'é');
});

test('missing generated files are skipped without creation', (t) => {
  const path = join(fixture(t), 'missing.ts');
  assert.equal(readOptionalGeneratedFile(path), null);
  assert.equal(rewriteGeneratedFile(path, () => { throw new Error('not called'); }), false);
});

test('refuses symlink reads, writes, and exclusive creation', (t) => {
  const directory = fixture(t);
  const victim = join(directory, 'victim');
  const path = join(directory, 'model.ts');
  writeFileSync(victim, 'private control');
  symlinkSync(victim, path);
  assert.throws(() => readOptionalGeneratedFile(path));
  assert.throws(() => rewriteGeneratedFile(path, () => 'attack'));
  assert.throws(() => createGeneratedFile(path, 'attack'));
  assert.equal(readFileSync(victim, 'utf8'), 'private control');
});

test('a path swap during transformation cannot redirect the write', (t) => {
  const directory = fixture(t);
  const path = join(directory, 'model.ts');
  const moved = join(directory, 'original.ts');
  const victim = join(directory, 'victim');
  writeFileSync(path, 'generated content');
  writeFileSync(victim, 'private control');
  rewriteGeneratedFile(path, (contents) => {
    assert.equal(contents, 'generated content');
    renameSync(path, moved);
    symlinkSync(victim, path);
    return 'updated';
  });
  assert.equal(readFileSync(moved, 'utf8'), 'updated');
  assert.equal(readFileSync(victim, 'utf8'), 'private control');
});

test('exclusive creation preserves an existing regular file', (t) => {
  const path = join(fixture(t), 'model.ts');
  createGeneratedFile(path, 'original');
  assert.throws(() => createGeneratedFile(path, 'replacement'), { code: 'EEXIST' });
  assert.equal(readFileSync(path, 'utf8'), 'original');
});

test('a rejected transformation leaves the original content intact', (t) => {
  const path = join(fixture(t), 'model.ts');
  createGeneratedFile(path, 'original');
  assert.throws(() => rewriteGeneratedFile(path, () => { throw new Error('changed contract'); }));
  assert.equal(readFileSync(path, 'utf8'), 'original');
});
