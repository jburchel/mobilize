module.exports = {
  plugins: [
    require('postcss-import'),
    require('postcss-nested'),
    require('postcss-preset-env')({
      stage: 1,
      features: {
        'nesting-rules': true,
      }
    }),
    require('autoprefixer'),
    process.env.NODE_ENV === 'production' ? 
      require('cssnano')({
        preset: ['default', {
          discardComments: {
            removeAll: true,
          },
        }]
      }) : false,
    process.env.NODE_ENV === 'production' ?
      require('@fullhuman/postcss-purgecss')({
        content: [
          './app/templates/**/*.html',
          './app/static/js/**/*.js'
        ],
        defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
        safelist: [
          /^modal/,
          /^tooltip/,
          /^popover/,
          /^dropdown/,
          /^alert/,
          /^btn/,
          /^collapse/,
          /^form/,
          /^nav/,
          /^badge/,
          /^card/,
          /^table/,
          /^is-/,
          /^has-/,
          /^active/,
          /^disabled/,
          /^show/,
          /^hide/,
          /^fade/,
          // Bootstrap-specific utility classes that might be dynamically added
          /^bg-/,
          /^text-/,
          /^border-/,
          /^rounded-/,
          /^d-/,
          /^p-/,
          /^m-/,
          /^w-/,
          /^h-/,
          /^shadow-/,
          /^position-/,
          // Common state classes
          /^is-invalid/,
          /^is-valid/,
          /^was-validated/
        ]
      }) : false
  ].filter(Boolean)
}; 