const autoprefixer = require('autoprefixer')
const concat = require('gulp-concat')
const cssnano = require('cssnano')
const del = require('del')
const eslint = require('gulp-eslint')
const gulp = require('gulp')
const gulpif = require('gulp-if')
const imagemin = require('gulp-imagemin')
const options = require('gulp-options')
const path = require('path')
const postcss = require('gulp-postcss')
const sass = require('gulp-dart-sass')
const spritesmith = require('gulp.spritesmith')
const terser = require('gulp-terser-js')
const fs = require('fs')


/* Speed mode */

// You can use '--speed' to speed the tasks, it disables some optimisations like minification
const fast = options.has('speed')
if (!fast) {
  console.log('The speed mode is not enabled.')
} else {
  console.log('The speed mode is enabled.')
}


/* SCSS tasks */

// Generates a sprite with the website icons
function spriteCss() {
  return gulp.src('assets/images/sprite/*.png')
    .pipe(spritesmith({
      cssTemplate: 'assets/scss/_sprite.scss.hbs',
      cssName: 'scss/_sprite.scss',
      imgName: 'images/sprite.png',
      retinaImgName: 'images/sprite@2x.png',
      retinaSrcFilter: 'assets/images/sprite/*@2x.png'
    }))
    .pipe(gulp.dest('dist/'))
}

// PostCSS settings
const postcssPlugins = [autoprefixer(), cssnano()]

// Node SASS settings
const customSass = () => sass({
  sourceMapContents: true,
  includePaths: [
    path.join(__dirname, 'node_modules'),
    path.join(__dirname, 'dist', 'scss')
  ]
}).on('error', sass.logError)

function customSassError(error) {
  if (error.plugin === 'gulp-sass') {
    terser.printError.call(this, {
      name: error.name,
      line: error.line,
      col: error.column,
      filePath: error.file,
      fileContent: '' + fs.readFileSync(error.file),
      message: (error.messageOriginal || '').replace(error.file, path.basename(error.file)).split(' in file')[0],
      plugin: error.plugin
    })
    console.log('Original message:', error.messageFormatted)
    this.emit('end')
  } else {
    console.log(error.message)
  }
  // TODO: https://github.com/A-312/gulp-terser-js#can-i-use-terser-to-format-error-of-an-other-gulp-module-
}

// Generates CSS for the website and the ebooks
function css() {
  return gulp.src(['assets/scss/main.scss', 'assets/scss/zmd.scss'], { sourcemaps: true })
    .pipe(customSass()) // SCSS to CSS
    .on('error', customSassError)
    .pipe(gulpif(!fast, postcss(postcssPlugins))) // Adds browsers prefixs and minifies
    .pipe(gulp.dest('dist/css/', { sourcemaps: '.' }))
}

// Generates CSS for the static error pages in the folder `errors/`
function errors() {
  return gulp.src('errors/scss/main.scss', { sourcemaps: true })
    .pipe(customSass())
    .on('error', customSassError)
    .pipe(gulpif(!fast, postcss(postcssPlugins)))
    .pipe(gulp.dest('errors/css/', { sourcemaps: '.' }))
}


/* JS tasks */

// ESLint options
var eslintOptions = {}
const fix = options.has('fix')
if (fix) {
  eslintOptions = { fix: true }
}

// Lints the JS source files

function jsLint() {
  return gulp.src(['assets/js/*.js', 'Gulpfile.js', '!assets/js/editor-old.js'], { base: '.' })
    .pipe(eslint(eslintOptions))
    .pipe(eslint.format())
    .pipe(gulp.dest('.'))
    .pipe(eslint.failAfterError())
}

// Get JS minified files from packages
function jsPackages() {
  return gulp.src([
    require.resolve('jquery/dist/jquery.min.js'),
    require.resolve('cookies-eu-banner/dist/cookies-eu-banner.min.js'),
    require.resolve('moment/min/moment.min.js'),
    require.resolve('moment/locale/fr.js'),
    require.resolve('chart.js/dist/Chart.min.js'),
    require.resolve('easymde/dist/easymde.min.js')
  ])
    .pipe(gulp.dest('dist/js/'))
}

// Generates JS for the website
function js() {
  return gulp.src([
    // Used by other scripts, must be first
    'assets/js/modal.js',
    'assets/js/tooltips.js',
    // All the scripts
    'assets/js/*.js'
  ], { base: '.', sourcemaps: true })
    .pipe(gulpif(!fast, terser())) // Minifies the JS
    .on('error', function(error) {
      if (error.plugin.startsWith('gulp-terser')) {
        this.emit('end')
      } else {
        console.log(error.message)
      }
    })
    .pipe(concat('script.js', { newLine: ';\r\n' })) // One JS file to rule them all
    .pipe(gulp.dest('dist/js/', { sourcemaps: '.' }))
}


/* Images tasks */

// Optimizes the images
function images() {
  var plugins = [
    imagemin.gifsicle(),
    imagemin.mozjpeg(),
    imagemin.optipng(),
    // Avoid over-optimizing svg animations
    imagemin.svgo({
      plugins: [
        { removeHiddenElems: false }
      ]
    })
  ]
  return gulp.src(['assets/{images,smileys,licenses}/**/*', '!assets/images/sprite/*.png'])
    .pipe(gulpif(!fast, imagemin(plugins))) // Minify the images
    .pipe(gulp.dest('dist/'))
}

function spriteImages() {
  return gulp.src(['dist/images/sprite*.png'])
    .pipe(gulpif(!fast, imagemin())) // Minify the images
    .pipe(gulp.dest('dist/images/'))
}


/* Other tasks */

// Prepares files for zmarkdown
function prepareZmd() {
  return gulp.src(['node_modules/katex/dist/{katex.min.css,fonts/*}'])
    .pipe(gulp.dest('dist/css/'))
}

// Prepares files for easy mde
function prepareEasyMde() {
  return gulp.src(['node_modules/easymde/dist/easymde.min.css'])
    .pipe(gulp.dest('dist/css/'))
}

// Deletes the generated files
function clean() {
  return del('dist/')
}


/* Commands */

// Watch for file changes
function watch() {
  gulp.watch('assets/js/*.js', js)
  gulp.watch(['assets/{images,smileys}/**/*', '!assets/images/sprite/*.png'], images)
  gulp.watch(['assets/scss/**/*.scss'], css)
  gulp.watch(['assets/images/sprite/*.png', 'assets/scss/_sprite.scss.hbs'], gulp.series(spriteCss, gulp.parallel(css, spriteImages)))
}

// Build the front
var build = gulp.parallel(prepareZmd, prepareEasyMde, jsPackages, js, images, gulp.series(spriteCss, gulp.parallel(css, spriteImages)))

exports.build = build
exports.watch = gulp.series(build, watch)
exports.lint = jsLint
exports.clean = clean
exports.errors = errors
exports.prepareZmd = prepareZmd
exports.prepareEasyMde = prepareEasyMde
exports.default = gulp.parallel(watch, jsLint)

