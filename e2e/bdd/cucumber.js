module.exports = {
  default: {
    require: ['step_definitions/**/*.js', 'support/**/*.js'],
    format: [
      'progress',
      'json:test-results/report.json'
    ],
    parallel: 1,
    timeout: 30000
  }
}
