import * as pdfjs from 'pdfjs-dist'
import workerSrc from 'pdfjs-dist/build/pdf.worker?worker&url'

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc

export async function pdfToText(url: string) {
  try {
    const pdf = await pdfjs.getDocument(url).promise

    let fullText = ''

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)

      const textContent = await page.getTextContent()

      const pageText = textContent.items.map(item => item.str).join(' ')
      fullText += pageText + '\n'
    }

    return fullText
  } catch (error) {
    return ''
  }
}

export async function checkPaper(url: string) {
  try {
    const response = await fetch(url, { method: 'HEAD' })
    const type = response.headers.get('Content-Type')

    return type !== null && type.toLowerCase() == 'application/pdf'
  } catch {
    return false
  }
}
