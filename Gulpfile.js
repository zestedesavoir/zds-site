const autoprefixer = require('autoprefixer');
const concat = require('gulp-concat');
const cssnano = require('cssnano');
const del = require('del');
const gulp = require('gulp');
const gulpif = require('gulp-if');
const imagemin = require('gulp-imagemin');
const jshint = require('gulp-jshint');
const options = require('gulp-options');
const path = require('path');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const spritesmith = require('gulp.spritesmith');
const uglify = require('gulp-uglify');


//// Speed mode

// You can use '--speed' to speed the tasks, it disables some optimisations like minification
const fast = options.has("speed");
if (!fast) {
    console.log("The speed mode is not enabled.");
} else {
    console.log("The speed mode is enabled.");
}


//// SCSS tasks

// Generates a sprite with the website icons
function sprite() {
    return gulp.src('assets/images/sprite/*.png')
        .pipe(spritesmith({
            cssTemplate: 'assets/scss/_sprite.scss.hbs',
            cssName: 'scss/_sprite.scss',
            imgName: 'images/sprite.png',
            retinaImgName: 'images/sprite@2x.png',
            retinaSrcFilter: 'assets/images/sprite/*@2x.png',
        }))
        .pipe(gulp.dest('dist/'));
}

// PostCSS settings
const postcssPlugins = [autoprefixer(), cssnano()];

// Node SASS settings
const customSass = () => sass({
    sourceMapContents: true,
    includePaths: [
        path.join(__dirname, 'node_modules'),
        path.join(__dirname, 'dist', 'scss'),
    ],
}).on('error', sass.logError);

// Generates CSS for the website and the ebooks
function css() {
    return gulp.src(['assets/scss/main.scss', 'assets/scss/zmd.scss'])
        .pipe(sourcemaps.init())
        .pipe(customSass()) // SCSS to CSS
        .pipe(gulpif(!fast, postcss(postcssPlugins))) // Adds browsers prefixs and minifies
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../../assets/scss/' }))
        .pipe(gulp.dest('dist/css/'));
}

// Generates CSS for the static error pages in the folder `errors/`
function errors() {
    return gulp.src('errors/scss/main.scss')
        .pipe(sourcemaps.init())
        .pipe(customSass())
        .pipe(gulpif(!fast, postcss(postcssPlugins)))
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../scss/' }))
        .pipe(gulp.dest('errors/css/'));
}


//// JS tasks

// Lints the JS source files
function js_lint() {
    return gulp.src([
        'assets/js/*.js',
        '!assets/js/editor.js', // We'll fix that later
    ])
        .pipe(jshint())
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'));
}

// Generates JS for the website
function js() {
    return gulp.src([
        require.resolve('jquery'),
        require.resolve('cookies-eu-banner'),
        require.resolve('moment/moment.js'),
        require.resolve('moment/locale/fr.js'),
        require.resolve('chart.js/dist/Chart.js'),
        // Used by other scripts, must be first
        'assets/js/modal.js',
        'assets/js/tooltips.js',
        // All the scripts
        'assets/js/*.js',
    ], { base: '.' })
        .pipe(sourcemaps.init({ loadMaps: true }))
        .pipe(concat('script.js', { newline: ';\r\n' })) // One JS file to rule them all
        .pipe(gulpif(!fast, uglify())) // Minifies the JS
        .on('error', function (err) {
            // gulp-uglify sucks
            console.log(err.toString());
        })
        .pipe(sourcemaps.write('.', { includeContent: true, sourceRoot: '../../' }))
        .pipe(gulp.dest('dist/js/'));
}


//// Other tasks

// Optimizes the images
function images() {
    return gulp.src('assets/{images,smileys,licenses}/**/*')
        .pipe(gulpif(!fast, imagemin())) // Minify the images
        .pipe(gulp.dest('dist/'));
}

// Prepares files for zmarkdown
function prepare_zmd() {
    return gulp.src(['node_modules/katex/dist/{katex.min.css,fonts/*}'])
        .pipe(gulp.dest('dist/css/'));
}

// Deletes the generated files
function clean() {
    return del('dist/');
}


//// Commands

// Watch for file changes
function watch() {
    gulp.watch('assets/js/*.js', js);
    gulp.watch(['assets/{images,smileys}/**/*', '!assets/images/sprite*.png'], images);
    gulp.watch(['assets/scss/**/*.scss', '!assets/scss/_sprite.scss'], css);
}

// Build the front
var build = gulp.parallel(prepare_zmd, js, gulp.series(sprite, gulp.parallel(css, images)));

exports.build = build;
exports.watch = gulp.series(build, watch);
exports.lint = js_lint;
exports.clean = clean;
exports.errors = errors;
exports.prepare_zmd = prepare_zmd;
exports.default = gulp.parallel(watch, js_lint);

