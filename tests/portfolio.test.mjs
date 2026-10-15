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
  test(`${slug} homepage links resolve to a runnable demo and evidence`, () => {
    const path = resolve(root,'projects',slug);
    assert.ok(existsSync(resolve(path, 'README.md')), `Missing project README for ${slug}`);
    assert.ok(existsSync(resolve(path, 'index.html')), `Missing project page for ${slug}`);
    const html=readFileSync(resolve(path,'index.html'),'utf8');
    const readme=readFileSync(resolve(path,'README.md'),'utf8');
    assert.match(html, /<html/i);
    assert.match(html, /<body/i);
    assert.match(readme, /synthetic|sint[eé]tic/i);
    assert.match(readme, /test|prueba/i);
    assert.match(readme, /limit|l[ií]mit/i);
    assert.ok(homepage.includes(`href="projects/${slug}/"`), `Homepage demo link missing for ${slug}`);
    assert.ok(homepage.includes(`/blob/main/projects/${slug}/README.md`), `Evidence link missing for ${slug}`);
    assert.ok(homepage.includes(`/tree/main/projects/${slug}`), `Source link missing for ${slug}`);
  });
}
