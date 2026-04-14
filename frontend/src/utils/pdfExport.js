const DEFAULT_TITLE = '剧本正文'
const ACT_SECTION_PATTERN = /^第[一二三四五六七八九十百零\d]+幕[·.、 ]?第[一二三四五六七八九十百零\d]+节$/
const SCENE_NUMBER_PATTERN = /^第[一二三四五六七八九十百零\d]+场$/
const SCENE_HEADING_PREFIXES = ['内景', '外景', '内外景', '外内景', '画外音']

export function sanitizeScreenplayText(text) {
  if (!text) return ''

  return String(text)
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/\t/g, '  ')
    .replace(/[^\S\n]+$/gm, '')
    .replace(/^[ \t]*#{1,6}[ \t]*/gm, '')
    .replace(/^[ \t]*>[ \t]*/gm, '')
    .replace(/^[ \t]*[-*]+[ \t]*/gm, '')
    .replace(/^[ \t]*\d+\.[ \t]*/gm, '')
    .replace(/[`*_~]/g, '')
    .replace(/\bINT\.\s*/gi, '内景 ')
    .replace(/\bEXT\.\s*/gi, '外景 ')
    .replace(/\bO\.S\.\b/gi, '画外音')
    .replace(/\(O\.S\.\)/gi, '画外音')
    .replace(/[ ]{2,}/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export function buildScreenplayTitle(inputTitle, content) {
  const title = String(inputTitle || '').trim()
  if (title) return title

  const candidate = sanitizeScreenplayText(content)
    .split('\n')
    .map((line) => line.trim())
    .find((line) => line && !isStructureLine(line))

  if (!candidate) return DEFAULT_TITLE
  return candidate.replace(/[\\/:*?"<>|]/g, '').slice(0, 24) || DEFAULT_TITLE
}

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function isSceneHeadingLine(line) {
  const trimmed = String(line || '').trim()
  return SCENE_HEADING_PREFIXES.some((prefix) => trimmed.startsWith(prefix))
}

function isStructureLine(line) {
  const trimmed = String(line || '').trim()
  return ACT_SECTION_PATTERN.test(trimmed) || SCENE_NUMBER_PATTERN.test(trimmed) || isSceneHeadingLine(trimmed)
}

function classifyScreenplayLine(line) {
  const trimmed = String(line || '').trim()
  if (!trimmed) return 'spacer'
  if (ACT_SECTION_PATTERN.test(trimmed)) return 'act-section'
  if (SCENE_NUMBER_PATTERN.test(trimmed)) return 'scene-number'
  if (isSceneHeadingLine(trimmed)) return 'scene-heading'
  return 'body'
}

function renderScreenplayContent(content) {
  const lines = sanitizeScreenplayText(content).split('\n')
  const parts = []

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    const type = classifyScreenplayLine(line)

    if (type === 'spacer') {
      parts.push('<div class="spacer"></div>')
      continue
    }

    if (type === 'scene-number') {
      let probeIndex = index + 1
      while (probeIndex < lines.length && classifyScreenplayLine(lines[probeIndex]) === 'spacer') {
        probeIndex += 1
      }
      const nextLine = lines[probeIndex] || ''
      const nextType = classifyScreenplayLine(nextLine)
      if (nextType === 'scene-heading') {
        parts.push(
          `<div class="scene-block">` +
            `<div class="scene-meta scene-number">${escapeHtml(line)}</div>` +
            `<div class="scene-meta scene-heading">${escapeHtml(nextLine)}</div>` +
          `</div>`
        )
        index = probeIndex
        while (index + 1 < lines.length && classifyScreenplayLine(lines[index + 1]) === 'spacer') {
          index += 1
        }
        continue
      }

      parts.push(`<div class="scene-block"><div class="scene-meta scene-number">${escapeHtml(line)}</div></div>`)
      while (index + 1 < lines.length && classifyScreenplayLine(lines[index + 1]) === 'spacer') {
        index += 1
      }
      continue
    }

    if (type === 'scene-heading') {
      parts.push(`<div class="scene-block"><div class="scene-meta scene-heading">${escapeHtml(line)}</div></div>`)
      while (index + 1 < lines.length && classifyScreenplayLine(lines[index + 1]) === 'spacer') {
        index += 1
      }
      continue
    }

    parts.push(`<p class="line ${type}">${escapeHtml(line)}</p>`)
  }

  return parts.join('')
}

export function openScreenplayPdfWindow({ title, content }) {
  const cleanContent = sanitizeScreenplayText(content)
  if (!cleanContent) return false

  const safeTitle = buildScreenplayTitle(title, cleanContent)
  const printWindow = window.open('', '_blank')
  if (!printWindow) return false

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(safeTitle)}.pdf</title>
    <style>
      @page {
        size: A4;
        margin: 18mm 16mm 18mm;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        color: #111827;
        background: #f3f4f6;
        font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "SimSun", sans-serif;
      }

      .page {
        width: 210mm;
        min-height: 297mm;
        margin: 0 auto;
        padding: 18mm 16mm;
        background: #ffffff;
      }

      .title {
        margin: 0 0 12mm;
        text-align: center;
        font-size: 26px;
        line-height: 1.35;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .content {
        color: #111827;
      }

      .line {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .act-section {
        margin-top: 9mm;
        margin-bottom: 3mm;
        font-size: 18px;
        line-height: 1.55;
        font-weight: 700;
        page-break-after: avoid;
      }

      .scene-number,
      .scene-heading {
        font-size: 16px;
        line-height: 1.8;
        font-weight: 400;
      }

      .scene-block {
        margin-bottom: 4.5mm;
        page-break-after: avoid;
      }

      .scene-meta {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .scene-block .scene-number,
      .scene-block .scene-heading {
        margin: 0;
      }

      .body {
        font-size: 13px;
        line-height: 1.92;
        font-weight: 400;
      }

      .spacer {
        height: 4mm;
      }

      @media print {
        body {
          background: #ffffff;
        }

        .page {
          width: auto;
          min-height: auto;
          margin: 0;
          padding: 0;
        }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <h1 class="title">${escapeHtml(safeTitle)}</h1>
      <section class="content">${renderScreenplayContent(cleanContent)}</section>
    </main>
    <script>
      window.onload = function () {
        setTimeout(function () {
          window.focus();
          window.print();
        }, 150);
      };
    </script>
  </body>
</html>`

  try {
    printWindow.document.open()
    printWindow.document.write(html)
    printWindow.document.close()
  } catch (error) {
    console.error(error)
    printWindow.close()
    return false
  }

  return true
}
