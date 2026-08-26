import { renderReportPages } from './renderReportPages.mjs'

renderReportPages()
  .then((r) => console.log('done', r))
  .catch((err) => {
    console.error(err)
    process.exitCode = 1
  })
