const DEFAULT_TITLE = '剧本正文'
const SCENE_HEADING_PATTERN = /^(第[一二三四五六七八九十百零0-9]+[场幕章节]|内景|外景|画外音)\b/

export function sanitizeScreenplayText(text) {
  if (!text) return ''

  return String(text)
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/\t/g, '  ')
    .replace(/[^\S\n]+$/gm, '')
    .replace(/^[ \t]*#{1,6}[ \t]*/gm, '')
    .replace(/^[ \t]*>[ \t]*/gm, '')
    .replace(/^[ \t]*[-*•]+[ \t]*/gm, '')
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
    .find((line) => line && !SCENE_HEADING_PATTERN.test(line))

  if (!candidate) return DEFAULT_TITLE

  return candidate.replace(/[\\/:*?"<>|]/g, '').slice(0, 24) || DEFAULT_TITLE
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
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
        font-size: 24px;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .content {
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 14px;
        line-height: 1.9;
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
      <section class="content">${escapeHtml(cleanContent)}</section>
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
