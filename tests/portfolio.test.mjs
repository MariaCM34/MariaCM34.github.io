import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const homepage = readFileSync(resolve(root,'index.html'),'utf8');

test('homepage has Spanish-English presentation and GitHub identity', () => {
  assert.match(homepage, /MariaCM34/);
  assert.match(homepage, /translations/);
  assert.match(homepage, /<html/);
});

test('homepage does not contain typical accidental secret patterns', () => {
  assert.doesNotMatch(homepage, /sk-(?:proj-)?[A-Za-z0-9]{24,}/);
  assert.doesNotMatch(homepage, /BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY/);
});

for (const slug of ['ask-your-data','energypulse','modernize-studio']) {
  test(`${slug} demo has a project README and runnable page only if implemented`, () => {
    const path = resolve(root,'projects',slug);
    assert.ok(existsSync(resolve(path, 'README.md')), `Missing project README for ${slug}`);
    if (existsSync(resolve(path, 'index.html'))) {
      const html=readFileSync(resolve(path,'index.html'),'utf8');
      assert.match(html, /<html/i);
      assert.match(html, /<body/i);
    }
  });
}
