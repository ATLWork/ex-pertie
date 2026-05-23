module.exports = {
  default: {
    require: ['step_definitions/**/*.js', 'support/**/*.js'],
    format: [
      'progress-bar',
      'json:test-results/report.json',
      'allure-cucumberjs:allure-results'
    ],
    formatOptions: {
      resultsDir: 'allure-results',
      links: {
        issue: {
          urlTemplate: 'https://github.com/yourrepo/issues/%s',
          type: 'jira'
        }
      }
    },
    parallel: 1,
    timeout: 30000
  }
}
