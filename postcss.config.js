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
    // Always enable cssnano, but with different settings based on environment
    require('cssnano')({
      preset: ['default', {
        discardComments: {
          removeAll: process.env.NODE_ENV === 'production',
        },
        // Add more aggressive optimizations for production
        ...(process.env.NODE_ENV === 'production' ? {
          minifyFontValues: true,
          minifyGradients: true,
          mergeRules: true,
          normalizeWhitespace: true,
          reduceInitial: true,
          reduceTransforms: true,
          svgo: true,
          minifySelectors: true
        } : {})
      }]
    }),
    // Configure PurgeCSS to run in both development and production
    // but with more aggressive settings in production
    require('@fullhuman/postcss-purgecss')({
      content: [
        './app/templates/**/*.html',
        './app/static/js/**/*.js',
        // Include JS files that might contain class references
        './app/**/*.py',  // Include Python files that might render templates with class names
      ],
      defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
      // Enable verbose output to debug in development but not in production
      rejected: process.env.NODE_ENV !== 'production',
      // Only remove unused CSS in production, safelist everything in development
      // to make development easier
      safelist: {
        standard: [
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
          /^was-validated/,
          // Custom design system classes that might be dynamically added
          /^sidebar/,
          /^breadcrumb/,
          /^dashboard/,
          /^pipeline/,
          /^stat-/,
          /^priority-/,
          // Animation classes
          /^transition-/,
          /^transform-/,
          /^animate-/,
          /^appear-/,
          // Interactive components
          /^draggable/,
          /^sortable/,
          /^selectable/,
          // Include all in development mode
          ...(process.env.NODE_ENV !== 'production' ? ['*'] : [])
        ],
        // Deep safelist for specific patterns with their children
        deep: [
          /modal/,
          /dropdown/,
          /sidebar/,
          /table/
        ],
        // Safelist patterns that match ID selectors
        greedy: [
          /^#/
        ]
      }
    }),
    // Add CSS Critical Split plugin after PurgeCSS
    process.env.NODE_ENV === 'production' ? 
      require('postcss-critical-split')({
        output: 'rest',  // To generate the non-critical CSS
        startTag: '<!-- critical:start -->',
        endTag: '<!-- critical:end -->',
        blockTag: 'critical',
        suffix: '',
        files: [
          {
            input: 'app/static/css/dist/styles.css',
            output: 'app/static/css/dist/styles.critical.css',
            startTag: '<!-- critical:start -->',
            endTag: '<!-- critical:end -->',
            blockTag: 'critical',
            suffix: '.critical'
          }
        ]
      }) : false
  ].filter(Boolean)
}; 