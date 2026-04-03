(function () {
  var BUTTON_ID = 'screenplay-export-pdf-button'
  var DEFAULT_TITLE = '剧本正文'
  var SCENE_HEADING_PATTERN = /^(第[一二三四五六七八九十百零0-9]+[场幕章节]|内景|外景|画外音)\b/

  function sanitizeScreenplayText(text) {
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

  async function getProjectTitle() {
    var candidates = ['/src/stores/project.js']
    if (window.location.pathname.indexOf('/ai-screenplay-system/') !== -1) {
      candidates.unshift('/ai-screenplay-system/assets/project-8da2a1e5.js')
    }

    for (var i = 0; i < candidates.length; i++) {
      try {
        var mod = await import(candidates[i])
        var state = mod && mod.g
        var title = state && state.title ? String(state.title).trim() : ''
        if (title) return title
      } catch (error) {
        console.debug(error)
      }
    }

    return ''
  }

  async function buildTitle(content) {
    var projectTitle = await getProjectTitle()
    if (projectTitle) return projectTitle

    var candidate = sanitizeScreenplayText(content)
      .split('\n')
      .map(function (line) { return line.trim() })
      .find(function (line) { return line && !SCENE_HEADING_PATTERN.test(line) })

    return (candidate || DEFAULT_TITLE).replace(/[\\/:*?"<>|]/g, '').slice(0, 24) || DEFAULT_TITLE
  }

  function readMonacoContent() {
    try {
      var models = window.monaco && window.monaco.editor && window.monaco.editor.getModels
        ? window.monaco.editor.getModels()
        : []
      if (models && models.length) {
        return models[0].getValue()
      }
    } catch (error) {
      console.error(error)
    }

    var lines = Array.prototype.slice
      .call(document.querySelectorAll('.monaco-editor .view-lines .view-line'))
      .map(function (line) {
        return (line.textContent || '').replace(/\u00a0/g, ' ')
      })

    return lines.join('\n')
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  }

  async function exportPdf() {
    var content = sanitizeScreenplayText(readMonacoContent())
    if (!content) {
      window.alert('请先在高级编辑器里输入剧本内容，再导出 PDF。')
      return
    }

    var title = await buildTitle(content)
    var printWindow = window.open('', '_blank')
    if (!printWindow) {
      window.alert('浏览器拦截了导出窗口，请允许弹窗后重试。')
      return
    }

    var html =
      '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8" />' +
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />' +
        '<title>' + escapeHtml(title) + '.pdf</title>' +
        '<style>@page{size:A4;margin:18mm 16mm 18mm;}*{box-sizing:border-box;}body{margin:0;color:#111827;background:#f3f4f6;font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","SimSun",sans-serif;}.page{width:210mm;min-height:297mm;margin:0 auto;padding:18mm 16mm;background:#fff;}.title{margin:0 0 12mm;text-align:center;font-size:24px;font-weight:700;letter-spacing:.04em;}.content{white-space:pre-wrap;word-break:break-word;font-size:14px;line-height:1.9;}@media print{body{background:#fff;}.page{width:auto;min-height:auto;margin:0;padding:0;}}</style>' +
        '</head><body><main class="page"><h1 class="title">' + escapeHtml(title) + '</h1><section class="content">' + escapeHtml(content) + '</section></main><script>window.onload=function(){setTimeout(function(){window.focus();window.print();},150);};<\/script></body></html>'

    try {
      printWindow.document.open()
      printWindow.document.write(html)
      printWindow.document.close()
    } catch (error) {
      console.error(error)
      printWindow.close()
      window.alert('导出窗口写入失败，请刷新页面后重试。')
    }
  }

  function ensureButton() {
    if (window.location.hash.indexOf('#/editor') !== 0) return

    var heroActions = document.querySelector('.editor-hero .hero-actions')
    if (!heroActions || document.getElementById(BUTTON_ID)) return

    var button = document.createElement('button')
    button.id = BUTTON_ID
    button.type = 'button'
    button.textContent = '导出 PDF'
    button.style.border = '1px solid rgba(255,255,255,0.2)'
    button.style.background = '#ffffff'
    button.style.color = '#12305c'
    button.style.borderRadius = '12px'
    button.style.padding = '10px 16px'
    button.style.fontSize = '14px'
    button.style.fontWeight = '600'
    button.style.cursor = 'pointer'
    button.style.boxShadow = '0 8px 20px rgba(0,0,0,0.12)'
    button.addEventListener('click', exportPdf)
    heroActions.appendChild(button)
  }

  function watchEditor() {
    ensureButton()
    var observer = new MutationObserver(ensureButton)
    observer.observe(document.body, { childList: true, subtree: true })
    window.addEventListener('hashchange', ensureButton)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', watchEditor)
  } else {
    watchEditor()
  }
})()
