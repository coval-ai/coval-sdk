import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { parse } from 'yaml';

const root = fileURLToPath(new URL('..', import.meta.url));
const output = join(root, 'dist/coval-openapi.yaml');

for (const document of ['metrics.yaml', './metrics.yaml', 'metrics-v1.yaml', 'missing.yaml']) {
  test(`bundles published cross-document reference ${document}`, (t) => {
    const catalogOperation = document === 'metrics-v1.yaml' ? 'listMetrics' : 'listCatalog';
    const directory = mkdtempSync(join(tmpdir(), 'bundle-spec-test-'));
    const previous = existsSync(output) ? readFileSync(output) : undefined;
    t.after(() => {
      rmSync(directory, { recursive: true, force: true });
      if (previous) writeFileSync(output, previous);
      else rmSync(output, { force: true });
    });
    writeFileSync(join(directory, 'metrics-v1.yaml'), `
openapi: 3.0.3
info: { title: Metrics, version: '1' }
paths:
  /metrics:
    get:
      operationId: listMetrics
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema: { $ref: '#/components/schemas/MetricResource' }
        '400': &error
          description: Error
          content:
            application/json:
              schema: { $ref: '#/components/schemas/MetricResource' }
        '404': *error
components:
  parameters:
    WorkspaceId: { name: workspace_id, in: query, schema: { type: string } }
  schemas:
    MetricResource: { type: object, properties: { id: { type: string } } }
`);
    writeFileSync(join(directory, 'metric-catalog-v1.yaml'), `
openapi: 3.0.3
info: { title: Catalog, version: '1' }
paths:
  /metrics/catalog:
    parameters:
      - $ref: '${document}#/components/parameters/WorkspaceId'
    get:
      operationId: ${catalogOperation}
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '${document}#/components/schemas/MetricResource' }
`);
    const result = spawnSync(process.execPath, ['scripts/bundle-spec.mjs'], {
      cwd: root, env: { ...process.env, COVAL_SPECS_DIR: directory }, encoding: 'utf8',
    });
    if (document === 'missing.yaml') {
      assert.notEqual(result.status, 0);
      assert.match(result.stdout + result.stderr, /missing\.yaml/);
      return;
    }
    assert.equal(result.status, 0, result.stdout + result.stderr);
    const bundle = parse(readFileSync(output, 'utf8'));
    const resolve = (reference) => {
      assert(reference.startsWith('#/'));
      return reference.slice(2).split('/').reduce(
        (value, part) => value[part.replaceAll('~1', '/').replaceAll('~0', '~')], bundle,
      );
    };
    const catalog = bundle.paths['/metrics/catalog'];
    assert.equal(resolve(catalog.parameters[0].$ref).name, 'workspace_id');
    const item = catalog.get.responses['200'].content['application/json'].schema.items.$ref;
    assert.equal(resolve(item).properties.id.type, 'string');
    const existing = bundle.paths['/metrics'].get;
    assert.equal(catalog.get.operationId, catalogOperation);
    assert.equal(existing.operationId, catalogOperation === 'listMetrics' ? 'metrics_listMetrics' : 'listMetrics');
    const existingRef = existing.responses['200'].content['application/json'].schema.$ref;
    assert.equal(existingRef, '#/components/schemas/Metrics_MetricResource');
    assert.deepEqual(resolve(existingRef), resolve(item));
    for (const status of ['400', '404']) {
      assert.equal(existing.responses[status].content['application/json'].schema.$ref, existingRef);
    }
  });
}
