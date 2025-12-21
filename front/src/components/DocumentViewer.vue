<template>
  <div class="document-viewer">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="content" class="document-content" v-html="renderedContent"></div>
    <div v-else class="empty">暂无内容</div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'DocumentViewer',
  props: {
    content: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const renderedContent = computed(() => {
      if (!props.content) return ''
      
      let content = props.content
      
      // 先处理表格（需要在其他处理之前）
      const lines = content.split('\n')
      const processedLines = []
      let i = 0
      
      while (i < lines.length) {
        const line = lines[i].trim()
        
        // 检查是否是表格行
        if (line.startsWith('|') && line.endsWith('|')) {
          const tableRows = []
          let headerRow = null
          let separatorRow = null
          let dataRows = []
          
          // 收集连续的表格行
          while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
            const currentLine = lines[i].trim()
            const cells = currentLine.split('|').map(cell => cell.trim()).filter(cell => cell)
            
            // 检查是否是分隔行（只包含 - 和 :）
            if (cells.every(cell => /^[\s\-:]+$/.test(cell))) {
              separatorRow = currentLine
            } else if (headerRow === null) {
              // 第一行是表头
              headerRow = cells
            } else {
              // 数据行
              dataRows.push(cells)
            }
            i++
          }
          
          // 如果有表头，生成表格HTML
          if (headerRow && separatorRow) {
            let tableHtml = '<table class="markdown-table"><thead><tr>'
            headerRow.forEach(cell => {
              // 处理粗体
              const cellContent = cell.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
              tableHtml += `<th>${cellContent}</th>`
            })
            tableHtml += '</tr></thead><tbody>'
            
            dataRows.forEach(row => {
              tableHtml += '<tr>'
              // 确保行数据与表头列数一致
              for (let j = 0; j < headerRow.length; j++) {
                const cellContent = (row[j] || '').replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
                tableHtml += `<td>${cellContent}</td>`
              }
              tableHtml += '</tr>'
            })
            
            tableHtml += '</tbody></table>'
            processedLines.push(tableHtml)
            continue
          }
        }
        
        // 非表格行，正常处理
        processedLines.push(lines[i])
        i++
      }
      
      // 重新组合内容
      content = processedLines.join('\n')
      
      // 处理其他Markdown格式
      let html = content
        // 标题
        .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // 粗体
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        // 无序列表
        .replace(/^[\-\*\+]\s+(.*$)/gim, '<li>$1</li>')
        // 有序列表
        .replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>')
        // 换行
        .replace(/\n\n/gim, '</p><p>')
        .replace(/\n/gim, '<br>')
      
      // 包装列表
      html = html.replace(/(<li>.*?<\/li>)/gim, '<ul>$1</ul>')
      html = html.replace(/<\/ul>\s*<ul>/gim, '')
      
      // 包装段落（排除已经是块级元素的）
      const blockElements = ['<h1', '<h2', '<h3', '<h4', '<table', '<ul', '<ol']
      const lines2 = html.split('<br>')
      const wrappedLines = []
      
      for (let line of lines2) {
        const trimmed = line.trim()
        if (!trimmed) {
          wrappedLines.push('')
          continue
        }
        
        const isBlockElement = blockElements.some(tag => trimmed.startsWith(tag))
        if (!isBlockElement && !trimmed.startsWith('<p>') && !trimmed.startsWith('</p>')) {
          wrappedLines.push(`<p>${trimmed}</p>`)
        } else {
          wrappedLines.push(trimmed)
        }
      }
      
      html = wrappedLines.join('')
      
      return html
    })

    return {
      renderedContent
    }
  }
}
</script>

<style scoped>
.document-viewer {
  width: 100%;
  height: 100%;
}

.document-content {
  padding: 24px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  line-height: 1.8;
  color: var(--text-primary);
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.document-content :deep(h1) {
  font-size: 24px;
  margin: 20px 0 16px;
  font-weight: 600;
}

.document-content :deep(h2) {
  font-size: 20px;
  margin: 18px 0 14px;
  font-weight: 600;
}

.document-content :deep(h3) {
  font-size: 18px;
  margin: 16px 0 12px;
  font-weight: 600;
}

.document-content :deep(p) {
  margin: 12px 0;
}

.document-content :deep(table.markdown-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.document-content :deep(table.markdown-table thead) {
  background-color: #f8f9fa;
}

.document-content :deep(table.markdown-table th) {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #212529;
  font-size: 14px;
}

.document-content :deep(table.markdown-table td) {
  border: 1px solid #dee2e6;
  padding: 12px 16px;
  text-align: left;
  color: #495057;
  vertical-align: top;
}

.document-content :deep(table.markdown-table tbody tr:nth-child(even)) {
  background-color: #f8f9fa;
}

.document-content :deep(table.markdown-table tbody tr:hover) {
  background-color: #e9ecef;
}

.document-content :deep(table.markdown-table th strong),
.document-content :deep(table.markdown-table td strong) {
  font-weight: 600;
  color: #212529;
}

.document-content :deep(ul) {
  margin: 12px 0;
  padding-left: 24px;
}

.document-content :deep(ul li) {
  margin: 6px 0;
  line-height: 1.6;
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}
</style>
