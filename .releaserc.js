module.exports = {
  branches: ["main", { name: "beta", channel: "beta", prerelease: true }, { name: "semantic_release", channel: "beta", prerelease: true }],
  plugins: [
    [
      '@semantic-release/commit-analyzer', {
        preset: 'angular',
        releaseRules: [
          // Example: `type(scope): subject [force release]`
          { subject: '*\\[force release\\]*', release: 'patch' },
        ],
      },
    ],
    '@semantic-release/release-notes-generator',
    '@semantic-release/changelog',
    //   [
    //   '@semantic-release/exec',
    //   {
    //     prepareCmd: 'sed -i \'s/version = .*/version = ${nextRelease.version}/g\' setup.cfg; sed -i \'s/"version": ".*"/"version": "${nextRelease.version}"/g\' package.json;',
    //     successCmd: 'touch .trigger-pypi-release',
    //   },
    // ],
    [
      '@semantic-release/git',
      {
        assets: [
          'CHANGELOG.md',
          'package.json',
          'src/agent_toolkit/pyproject.toml',
          'src/datasource_sqlalchemy/pyproject.toml',
          'src/datasource_toolkit/pyproject.toml',
          'src/flask_agent/pyproject.toml'
        ],
      },
    ],
    '@semantic-release/github',
    // [
    //   'semantic-release-slack-bot',
    //   {
    //     markdownReleaseNotes: true,
    //     notifyOnSuccess: true,
    //     notifyOnFail: false,
    //     onSuccessTemplate: {
    //       text: "📦 $package_name@$npm_package_version has been released!",
    //       blocks: [{
    //         type: 'section',
    //         text: {
    //           type: 'mrkdwn',
    //           text: '*New `$package_name` package released!*'
    //         }
    //       }, {
    //         type: 'context',
    //         elements: [{
    //           type: 'mrkdwn',
    //           text: "📦  *Version:* <$repo_url/releases/tag/$npm_package_version|$npm_package_version>"
    //         }]
    //       }, {
    //         type: 'divider',
    //       }],
    //       attachments: [{
    //         blocks: [{
    //           type: 'section',
    //           text: {
    //             type: 'mrkdwn',
    //             text: '*Changes* of version $release_notes',
    //           },
    //         }],
    //       }],
    //     },
    //     packageName: 'agent-python',
    //   }
    // ],
  ]
}
