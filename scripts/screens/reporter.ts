import { mkdir, writeFile } from 'node:fs/promises';
import type { FullResult, Reporter, TestCase, TestResult } from '@playwright/test/reporter';

const escape = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!,
  );

type Capture = Record<string, unknown> & {
  project: string;
  screen: string;
  status: string;
  errors: (string | undefined)[];
};
const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

export default class ScreensReporter implements Reporter {
  private captures: Capture[] = [];

  onTestEnd(test: TestCase, result: TestResult) {
    const capture = result.attachments.find((item) => item.name === 'capture');
    const decoded: unknown = capture?.body ? JSON.parse(capture.body.toString()) : null;
    const metadata = isRecord(decoded) ? decoded : {};
    this.captures.push({
      ...metadata,
      project: test.parent.project()?.name ?? 'unknown',
      screen: test.title,
      status: result.status,
      errors: result.errors.map((error) => error.message ?? error.value),
    });
  }

  async onEnd(result: FullResult) {
    this.captures.sort((a, b) =>
      `${a.project}/${a.screen}`.localeCompare(`${b.project}/${b.screen}`),
    );
    await mkdir('artifacts/screens', { recursive: true });
    await writeFile(
      'artifacts/screens/manifest.json',
      JSON.stringify(
        {
          status: result.status,
          commit: process.env.GITHUB_SHA ?? process.env.SCREENS_COMMIT ?? null,
          browser: 'Chromium',
          deviceScaleFactor: 1,
          note: 'Disposable local web export; UTC; simulated day/night and reduced motion. No native device coverage or automatic pixel-difference approval.',
          captures: this.captures,
        },
        null,
        2,
      ) + '\n',
    );
    const cards = this.captures
      .map((capture) => {
        const title = `${capture.project} / ${capture.screen}`;
        const image =
          typeof capture.image === 'string'
            ? `<a href="${escape(capture.image)}"><img loading="lazy" src="${escape(capture.image)}" alt="${escape(title)}"></a>`
            : '<p>No capture. See the test report.</p>';
        return `<article><h2>${escape(title)}</h2><p>${escape(capture.status)}</p>${image}<pre>${escape(JSON.stringify({ diagnostics: capture.diagnostics, errors: capture.errors }, null, 2))}</pre></article>`;
      })
      .join('\n');
    await writeFile(
      'artifacts/screens/index.html',
      `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NapAttack screenshot review</title><style>body{font:16px system-ui;margin:20px;background:#f4f1e8;color:#242824}h1{font-size:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px}article{border:1px solid #65705e;padding:12px;background:white;min-width:0}h2{font-size:16px}img{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}</style><h1>NapAttack screenshot review</h1><p>${this.captures.length} captures · ${escape(result.status)} · <a href="manifest.json">Manifest</a> · <a href="report/index.html">Test report</a></p><p>Rendered web captures for visual review. These are not native-device tests or an automatic judgement of artwork.</p><main>${cards}</main></html>`,
    );
  }
}
